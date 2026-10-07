/**
 * The 2-second brand splash. It is presentational only — the app renders
 * behind it (and boot-swaps to skeletons under the mask), then it fades.
 */
export function Splash({ leaving }: { leaving: boolean }) {
  return (
    <div
      aria-hidden="true"
      className={`bg-gradient-navy fixed inset-0 z-[100] flex items-center justify-center overflow-hidden transition-opacity duration-500 ${
        leaving ? 'pointer-events-none opacity-0' : 'opacity-100'
      }`}
    >
      <div className="glow-blob -left-24 -top-24 h-[26rem] w-[26rem] bg-[var(--primary)]/50" />
      <div
        className="glow-blob -bottom-32 -right-20 h-96 w-96 bg-[var(--cyan)]/40"
        style={{ animationDelay: '1.1s' }}
      />
      <div className="anim-pop flex flex-col items-center text-center">
        <img
          src="/ajo-mark.png"
          alt=""
          className="h-14 w-auto drop-shadow-[0_18px_36px_color-mix(in_oklab,var(--deep)_40%,transparent)]"
        />
        <p className="font-display mt-5 text-sm font-semibold tracking-[0.45em] text-white/60">
          AJO.NG
        </p>
        <p className="font-display mt-1 text-lg text-white/80">Your Ajo. Your Story.</p>
      </div>
    </div>
  );
}