import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

interface LiquidGlassProps {
  children: React.ReactNode
  className?: string
}

export function LiquidGlass({ children, className = '' }: LiquidGlassProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const onMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width) * 100
      const y = ((e.clientY - rect.top) / rect.height) * 100
      el.style.setProperty('--mx', `${x}%`)
      el.style.setProperty('--my', `${y}%`)
    }

    el.addEventListener('mousemove', onMove)
    return () => el.removeEventListener('mousemove', onMove)
  }, [])

  return (
    <div
      ref={ref}
      style={
        {
          '--mx': '50%',
          '--my': '50%',
        } as React.CSSProperties
      }
      className={[
        'relative overflow-hidden rounded-2xl',
        // layered glass look
        'bg-white/5',
        'backdrop-blur-xl',
        'border border-white/10',
        'shadow-[0_8px_32px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.08)]',
        // liquid highlight that follows the cursor
        'before:pointer-events-none before:absolute before:inset-0',
        'before:rounded-[inherit]',
        'before:bg-[radial-gradient(circle_at_var(--mx)_var(--my),rgba(255,255,255,0.12)_0%,transparent_60%)]',
        'before:transition-opacity before:duration-300',
        // refraction edge shimmer
        'after:pointer-events-none after:absolute after:inset-0',
        'after:rounded-[inherit]',
        'after:bg-[linear-gradient(135deg,rgba(255,255,255,0.06)_0%,transparent_50%,rgba(255,255,255,0.03)_100%)]',
        className,
      ].join(' ')}
    >
      {children}
    </div>
  )
}

export function LiquidGlassDemo() {
  return (
    <section className="relative py-20">
      {/* background blobs to show off the glass effect */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute top-10 left-1/4 h-64 w-64 rounded-full bg-emerald-400/20 blur-[80px]" />
        <div className="absolute bottom-10 right-1/4 h-80 w-80 rounded-full bg-green-500/15 blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full bg-teal-400/10 blur-[60px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6">

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* Card 1 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <LiquidGlass className="p-8">
              <p className="mb-3 font-mono text-xs tracking-widest text-ember">01</p>
              <h3 className="mb-2 font-sans text-xl font-bold text-paper">Live voice AI</h3>
              <p className="text-sm leading-relaxed text-paper-dim">
                Speaks, interrupts, and adapts. Move your cursor over this card.
              </p>
            </LiquidGlass>
          </motion.div>

          {/* Card 2 — taller to show depth */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <LiquidGlass className="p-8">
              <p className="mb-3 font-mono text-xs tracking-widest text-ember">02</p>
              <h3 className="mb-2 font-sans text-xl font-bold text-paper">Real code</h3>
              <p className="text-sm leading-relaxed text-paper-dim">
                Monaco editor, multi-language, real test execution.
              </p>
              <div className="mt-5 rounded-lg bg-white/5 px-4 py-3 font-mono text-xs text-paper-dim">
                <span className="text-ember">def</span> two_sum(nums, target):<br />
                &nbsp;&nbsp;seen = &#123;&#125;<br />
                &nbsp;&nbsp;<span className="text-ember">for</span> i, n <span className="text-ember">in</span> enumerate(nums):<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-paper-faint"># …</span>
              </div>
            </LiquidGlass>
          </motion.div>

          {/* Card 3 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <LiquidGlass className="p-8">
              <p className="mb-3 font-mono text-xs tracking-widest text-ember">03</p>
              <h3 className="mb-2 font-sans text-xl font-bold text-paper">Feedback</h3>
              <p className="text-sm leading-relaxed text-paper-dim">
                Every score tied to a transcript moment.
              </p>
              <div className="mt-5 space-y-2">
                {[['Clarity', 82], ['Confidence', 71], ['Technical', 79]].map(([label, val]) => (
                  <div key={label} className="flex items-center justify-between">
                    <span className="font-mono text-xs text-paper-faint">{label}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-1 w-24 overflow-hidden rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-ember"
                          style={{ width: `${val}%` }}
                        />
                      </div>
                      <span className="font-mono text-xs text-ember">{val}</span>
                    </div>
                  </div>
                ))}
              </div>
            </LiquidGlass>
          </motion.div>
        </div>

        {/* Wide banner card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-6"
        >
        </motion.div>
      </div>
    </section>
  )
}
