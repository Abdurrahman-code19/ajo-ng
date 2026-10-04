import type pg from 'pg';
import type { FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import { ValidationError } from './identity.js';
import {
  acceptInvitation,
  declineInvitation,
  createInvitations,
  InvitationConflictError,
  InvitationGoneError,
  InvitationNotAllowedError,
  InvitationNotFoundError,
  listInvitations,
  previewInvitationByToken,
  type CreateInvitationInput,
} from './invitations.js';
import { requireIdentity } from './auth.js';

export interface InvitationRouteDeps {
  readonly pool: pg.Pool;
}

export function registerInvitationRoutes(app: FastifyInstance, deps: InvitationRouteDeps) {
  app.post('/api/v1/invitations', async (req: FastifyRequest, res: FastifyReply) => {
    try {
      const identity = await requireIdentity(req);
      const result = await createInvitations(deps.pool, identity, req.body as CreateInvitationInput);
      res.status(202).send(result);
      return;
    } catch (e) {
      if (e instanceof ValidationError) {
        res.status(422).send({ error: e.message, field: e.field });
        return;
      }
      if (e instanceof InvitationNotAllowedError) {
        res.status(403).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationConflictError) {
        res.status(409).send({ error: e.message });
        return;
      }
      res.status(500).send({ error: 'internal server error' });
      return;
    }
  });

  app.get('/api/v1/invitations', async (req: FastifyRequest, res: FastifyReply) => {
    try {
      const identity = await requireIdentity(req);
      const q = req.query as any;
      const ajoId = typeof q?.ajoId === 'string' ? q.ajoId : null;
      if (ajoId === null || ajoId.length === 0) {
        res.status(422).send({ error: 'ajoId is required', field: 'ajoId' });
        return;
      }
      const rows = await listInvitations(deps.pool, identity, ajoId);
      res.status(200).send({ invitations: rows });
      return;
    } catch (e) {
      if (e instanceof InvitationNotAllowedError) {
        res.status(403).send({ error: e.message });
        return;
      }
      res.status(500).send({ error: 'internal server error' });
      return;
    }
  });

  app.get('/api/v1/invitations/:token', async (req: FastifyRequest<{ Params: { token: string } }>, res: FastifyReply) => {
    try {
      const token = req.params.token;
      if (typeof token !== 'string' || token.length < 10) {
        res.status(404).send({ error: 'invitation not found' });
        return;
      }
      const preview = await previewInvitationByToken(deps.pool, token);
      res.status(200).send(preview);
      return;
    } catch (e) {
      if (e instanceof InvitationNotFoundError) {
        res.status(404).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationGoneError) {
        res.status(410).send({ error: `invitation is ${e.message.split(' ')[2] || e.message}` });
        return;
      }
      res.status(500).send({ error: 'internal server error' });
      return;
    }
  });

  app.post('/api/v1/invitations/accept', async (req: FastifyRequest, res: FastifyReply) => {
    try {
      const identity = await requireIdentity(req);
      const result = await acceptInvitation(deps.pool, identity, req.body as any);
      res.status(200).send(result);
      return;
    } catch (e) {
      if (e instanceof ValidationError) {
        res.status(422).send({ error: e.message, field: e.field });
        return;
      }
      if (e instanceof InvitationNotAllowedError) {
        res.status(403).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationConflictError) {
        res.status(409).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationNotFoundError) {
        res.status(404).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationGoneError) {
        res.status(410).send({ error: `invitation is ${e.message.split(' ')[2] || e.message}` });
        return;
      }
      res.status(500).send({ error: 'internal server error' });
      return;
    }
  });

  app.post('/api/v1/invitations/:token/decline', async (req: FastifyRequest<{ Params: { token: string } }>, res: FastifyReply) => {
    try {
      const identity = await requireIdentity(req);
      const token = req.params.token;
      const result = await declineInvitation(deps.pool, identity, token);
      res.status(200).send(result);
      return;
    } catch (e) {
      if (e instanceof ValidationError) {
        res.status(422).send({ error: e.message, field: e.field });
        return;
      }
      if (e instanceof InvitationNotAllowedError) {
        res.status(403).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationConflictError) {
        res.status(409).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationNotFoundError) {
        res.status(404).send({ error: e.message });
        return;
      }
      if (e instanceof InvitationGoneError) {
        res.status(410).send({ error: `invitation is ${e.message.split(' ')[2] || e.message}` });
        return;
      }
      res.status(500).send({ error: 'internal server error' });
      return;
    }
  });
}

