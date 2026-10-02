/**
 * The raw bytes of a request, for anything that signs them.
 *
 * §13.5 requires the HMAC to be computed over the raw body. Fastify's default
 * JSON parser throws the bytes away after parsing, and a signature checked over
 * a re-serialised object is not a signature check: JSON has no canonical form,
 * so key order and whitespace decide the digest. The two would disagree, and the
 * failure would look like a provider bug rather than ours.
 *
 * So the raw body is kept. Doing it with a second content-type parser is not
 * possible -- Fastify resolves one parser per content type, and the webhook is
 * `application/json` like everything else -- which means the replacement below
 * has to behave exactly like the one it replaces. It parses identically; the only
 * difference is that the text survives on `request.rawBody`.
 */
import type { FastifyInstance, FastifyRequest } from 'fastify';

/** The body as received, as text. Present only when the request had a JSON body. */
export type RequestWithRawBody = FastifyRequest & { rawBody?: string };

/**
 * The parser's own view of the request.
 *
 * A cast at one place rather than a declaration merge on `FastifyRequest`. Merging
 * would put `rawBody` on every request in the type system, including the ones on
 * routes that never read it, and the point of the intersection type is that a
 * route which needs the bytes has to say so.
 */
type ParserRequest = FastifyRequest & { rawBody?: string };

export function preserveRawBody(app: FastifyInstance): void {
  app.addContentTypeParser(
    'application/json',
    { parseAs: 'buffer' },
    (request, body: Buffer, done) => {
      const target = request as ParserRequest;
      target.rawBody = body.toString('utf8');
      if (body.length === 0) {
        // Fastify treats an empty body as absent rather than as invalid JSON, and
        // a POST with no body is a legitimate way to fail a required-body schema.
        done(null, undefined);
        return;
      }
      try {
        done(null, JSON.parse(target.rawBody) as unknown);
      } catch {
        // Deliberately *not* an error.
        //
        // §13.5 says to parse JSON only after the signature verifies, and the
        // adapter is the only party that can verify it. A parser that rejected
        // unparseable JSON here would run before the signature was ever checked,
        // which both parses unauthenticated input and turns "signed correctly,
        // unreadable bytes" into a 400 -- when the signature has already proved
        // the bytes are the provider's, and the right answer is to log it and
        // acknowledge.
        //
        // Handing the raw string on instead keeps that decision with the adapter.
        // Every other route has a body schema, so an unparseable body arrives
        // there as a string where an object is required and is still a 400 --
        // which is the same status the parse would have produced, reached without
        // the parser having opinions about the body before anyone authenticated it.
        done(null, target.rawBody);
      }
    },
  );
}