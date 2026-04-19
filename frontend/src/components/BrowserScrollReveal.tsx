import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'

function ProblemPanel() {
  return (
    <div className="border-r border-ink-700/40 bg-ink-950 p-5 overflow-hidden">
      <div className="flex items-center gap-2 mb-4">
        <span className="font-mono text-xs font-semibold text-paper">Two Sum</span>
        <span className="font-mono text-[9px] text-moss border border-moss/30 bg-moss/10 px-1.5 py-0.5 rounded-sm">
          Easy
        </span>
      </div>
      <div className="space-y-2 mb-5">
        {[82, 64, 91, 73, 55, 80, 68].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ink-700/70" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="border-l-2 border-ember/25 bg-ink-800/50 rounded-sm px-3 py-2.5 mb-4">
        <p className="font-mono text-[9px] text-paper-faint mb-2 uppercase tracking-widest">Example 1</p>
        {[72, 52].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ember/20 mb-1.5" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="space-y-2">
        {[78, 58, 88].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ink-700/60" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="mt-6 pt-4 border-t border-ink-700/40">
        <p className="font-mono text-[9px] text-paper-faint uppercase tracking-widest mb-2">Constraints</p>
        {[65, 45, 70].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ink-700/50 mb-1.5" style={{ width: `${w}%` }} />
        ))}
      </div>
    </div>
  )
}

function EditorPanel() {
  const lines = [
    { color: 'bg-purple-400/35', w: '85%' },
    { color: 'bg-paper/18', w: '70%' },
    { color: 'bg-ember/28', w: '60%' },
    { color: 'bg-ink-600/50', w: '38%' },
    { color: 'bg-moss/28', w: '82%' },
    { color: 'bg-paper/18', w: '55%' },
    { color: 'bg-ember/22', w: '74%' },
    { color: 'bg-ink-600/50', w: '88%' },
    { color: 'bg-moss/20', w: '50%' },
    { color: 'bg-paper/15', w: '62%' },
    { color: 'bg-ember/18', w: '44%' },
    { color: 'bg-ink-600/40', w: '72%' },
    { color: 'bg-purple-400/25', w: '58%' },
    { color: 'bg-paper/15', w: '80%' },
  ]
  return (
    <div className="border-r border-ink-700/40 bg-[#060608]">
      <div className="flex items-center gap-1 px-3 py-2.5 border-b border-ink-700/40 bg-ink-900/40">
        <span className="font-mono text-[10px] text-ember/65 border-b border-ember/35 px-2 pb-px">solution.py</span>
        <span className="font-mono text-[10px] text-paper-faint/35 px-2">tests.py</span>
        <span className="ml-auto font-mono text-[10px] text-paper-faint/35">Python 3</span>
      </div>
      <div className="p-4">
        {lines.map(({ color, w }, i) => (
          <div key={i} className="flex items-center gap-3 mb-3">
            <span className="font-mono text-[9px] text-ink-600/80 w-4 text-right shrink-0 select-none">{i + 1}</span>
            <div className={`h-1.5 rounded-sm ${color}`} style={{ width: w }} />
          </div>
        ))}
      </div>
    </div>
  )
}

function ChatPanel() {
  return (
    <div className="bg-ink-950 p-4 flex flex-col gap-2.5 overflow-hidden">
      <div className="flex items-center gap-2 mb-1.5">
        <div className="w-2 h-2 rounded-full bg-ember animate-pulse-ember shrink-0" />
        <span className="font-mono text-[10px] text-ember/65">Jordan · AI Interviewer</span>
      </div>
      <div className="bg-ink-800/80 border border-ink-700/50 rounded-sm p-3 space-y-1.5">
        {[100, 88, 62].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ink-600/55" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="self-end bg-ink-800/50 border border-ember/12 rounded-sm p-3 space-y-1.5 w-[88%]">
        {[100, 72].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ember/22" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="bg-ink-800/80 border border-ink-700/50 rounded-sm p-3 space-y-1.5">
        {[88, 65].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ink-600/55" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="self-end bg-ink-800/50 border border-ember/12 rounded-sm p-3 space-y-1.5 w-[80%]">
        {[100, 60].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ember/22" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="bg-ink-800/80 border border-ink-700/50 rounded-sm p-3 space-y-1.5">
        {[92, 75, 55].map((w, i) => (
          <div key={i} className="h-1.5 rounded-sm bg-ink-600/55" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="mt-auto border border-ink-700/50 rounded-sm px-3 py-2 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-ember/35 shrink-0" />
        <div className="flex-1 h-1 bg-ink-700/35 rounded-sm" />
      </div>
    </div>
  )
}

export function BrowserScrollReveal() {
  // Ref sits on the browser container itself — so progress 0 = browser
  // just entering the viewport from below, not the section headline.
  const browserRef = useRef<HTMLDivElement>(null)

  const { scrollYProgress } = useScroll({
    target: browserRef,
    offset: ['start end', 'end start'],
  })

  // Rise into frame as browser enters (0 → 0.25)
  const browserY  = useTransform(scrollYProgress, [0, 0.25], [80, 0])
  const browserOp = useTransform(scrollYProgress, [0, 0.2],  [0, 1])

  // Tilt unfolds while browser is in view (0 → 0.45)
  const rotateX   = useTransform(scrollYProgress, [0, 0.45], [22, 0])

  // Glare sweeps once mid-unfold (0.15 → 0.42)
  const glareX  = useTransform(scrollYProgress, [0.15, 0.42], ['-110%', '210%'])
  const glareOp = useTransform(scrollYProgress, [0.15, 0.28, 0.42], [0, 0.28, 0])

  // Ambient glow after landing (0.45 → 0.58)
  const glowOp = useTransform(scrollYProgress, [0.45, 0.58], [0, 1])

  // Labels staggered after browser is flat (0.48 → 0.72)
  const l1Op = useTransform(scrollYProgress, [0.48, 0.58], [0, 1])
  const l1Y  = useTransform(scrollYProgress, [0.48, 0.58], [10, 0])
  const l2Op = useTransform(scrollYProgress, [0.53, 0.63], [0, 1])
  const l2Y  = useTransform(scrollYProgress, [0.53, 0.63], [10, 0])
  const l3Op = useTransform(scrollYProgress, [0.58, 0.68], [0, 1])
  const l3Y  = useTransform(scrollYProgress, [0.58, 0.68], [10, 0])

  return (
    <section className="relative py-28">
      {/* Headline */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-60px' }}
        transition={{ duration: 0.55, ease: 'easeOut' }}
        className="text-center mb-16 px-6"
      >
        <p className="font-mono text-xs uppercase tracking-widest text-ember mb-5">
          ▶ watch it in action
        </p>
        <h2 className="font-display text-[clamp(2.4rem,5vw,4rem)] font-semibold text-paper leading-[1.05] tracking-tight">
          The whole interview,<br />in one view.
        </h2>
        <p className="mt-4 text-paper-dim text-base max-w-sm mx-auto leading-relaxed">
          Problem, code, and your AI interviewer — all live, all connected.
        </p>
      </motion.div>

      {/* Browser + labels */}
      <div className="relative mx-auto max-w-5xl px-16">

        {/* Label — left */}
        <motion.div
          style={{ opacity: l1Op, y: l1Y }}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 hidden lg:flex items-center gap-2"
        >
          <span className="font-mono text-[10px] text-paper-faint border border-ink-700/70 bg-ink-900 rounded-sm px-2.5 py-1 whitespace-nowrap">
            Problem statement
          </span>
          <div className="w-5 h-px bg-ink-700/40" />
        </motion.div>

        {/* Label — top center */}
        <motion.div
          style={{ opacity: l2Op, y: l2Y }}
          className="absolute left-1/2 -translate-x-1/2 -top-7 z-10 hidden lg:block"
        >
          <span className="font-mono text-[10px] text-ember/60 border border-ember/28 bg-ink-900 rounded-sm px-2.5 py-1 whitespace-nowrap">
            Monaco editor
          </span>
        </motion.div>

        {/* Label — right */}
        <motion.div
          style={{ opacity: l3Op, y: l3Y }}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 hidden lg:flex items-center gap-2"
        >
          <div className="w-5 h-px bg-ink-700/40" />
          <span className="font-mono text-[10px] text-paper-faint border border-ink-700/70 bg-ink-900 rounded-sm px-2.5 py-1 whitespace-nowrap">
            AI interviewer
          </span>
        </motion.div>

        {/* Browser — ref here so progress 0 = browser enters viewport */}
        <div ref={browserRef}>
        <motion.div
          style={{
            transformPerspective: 1200,
            rotateX,
            y: browserY,
            opacity: browserOp,
            transformOrigin: 'bottom center',
          }}
          className="w-full rounded-lg border border-ink-700/70 bg-ink-900 overflow-hidden relative shadow-card"
        >
            {/* Glare */}
            <motion.div
              aria-hidden
              style={{ x: glareX, opacity: glareOp }}
              className="absolute inset-0 z-20 pointer-events-none"
            >
              <div
                className="absolute inset-0"
                style={{
                  background:
                    'linear-gradient(108deg, transparent 38%, rgba(255,255,255,0.07) 50%, transparent 62%)',
                }}
              />
            </motion.div>

            {/* Browser chrome */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-ink-700/50 bg-ink-800/80">
              <span className="w-3 h-3 rounded-full bg-[#FF5F57] shrink-0" />
              <span className="w-3 h-3 rounded-full bg-[#FEBC2E] shrink-0" />
              <span className="w-3 h-3 rounded-full bg-[#28C840] shrink-0" />
              <div className="flex-1 mx-3 h-6 bg-ink-900/80 rounded-sm flex items-center justify-center border border-ink-700/30">
                <span className="font-mono text-[10px] text-paper-faint/50">
                  interview.app / session · Two Sum
                </span>
              </div>
              <span className="font-mono text-[10px] text-ember/55 shrink-0">● LIVE</span>
            </div>

            {/* 3-column body */}
            <div className="grid grid-cols-[200px_1fr_200px] min-h-[340px]">
              <ProblemPanel />
              <EditorPanel />
              <ChatPanel />
            </div>
        </motion.div>
        </div>

        {/* Ambient glow */}
        <motion.div
          aria-hidden
          style={{ opacity: glowOp }}
          className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-3/5 pointer-events-none"
        >
          <div
            style={{
              height: '8px',
              background: 'radial-gradient(ellipse, rgba(74,222,128,0.15) 0%, transparent 70%)',
              filter: 'blur(6px)',
            }}
          />
        </motion.div>
      </div>
    </section>
  )
}
