import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BrowserScrollReveal } from '../components/BrowserScrollReveal'
import { LiquidGlass } from '../components/LiquidGlass'

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
}
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: "easeOut" as const } as const},
}

const sampleTranscript = [
  { speaker: 'I', text: "Walk me through your approach before you start coding.", highlight: false },
  { speaker: 'U', text: "So my first instinct is brute force — O(n²) — but we can do better. I'd use a hash map to store complements as I iterate.", highlight: true },
  { speaker: 'I', text: "What's the space complexity of that?", highlight: false },
  { speaker: 'U', text: "O(n) in the worst case. Each element gets one entry in the map.", highlight: true },
  { speaker: 'I', text: "Good. I'll stop you there — one more thing: what about duplicate values?", highlight: false },
]

const features = [
  {
    num: '01',
    title: 'Live voice interviewer',
    body: 'A real-time AI interviewer that speaks, interrupts, probes, and adapts based on your answers. Not a chatbot.',
  },
  {
    num: '02',
    title: 'Real code, real tests',
    body: 'Full LeetCode-style editor with multi-language support, test execution, and complexity analysis.',
  },
  {
    num: '03',
    title: 'Evidence-based feedback',
    body: 'Every score is anchored to a specific transcript moment. You see exactly where you lost or earned points.',
  },
]

const companies = ['Google', 'Meta', 'Amazon', 'Apple', 'Microsoft', 'Stripe', 'Netflix', 'Airbnb']

export function Home() {
  const navigate = useNavigate()

  return (
    <div className="relative overflow-hidden">
      {/* Atmospheric background */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-[600px] w-[600px] rounded-full bg-ember/4 blur-[140px]" />
      </div>

      {/* Hero */}
      <section className="relative mx-auto max-w-7xl px-6 pt-20 pb-24 md:pt-32 md:pb-36">
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:gap-24"
        >
          {/* Left: text */}
          <div className="flex flex-col justify-center">
            <motion.p variants={fadeUp} className="mb-6 font-mono text-xs uppercase tracking-widest text-paper-faint">
              <span className="text-ember">▶</span> session.active
            </motion.p>

            <motion.h1
              variants={fadeUp}
              className="font-sans text-[clamp(2.8rem,6vw,5rem)] font-extrabold leading-[0.96] tracking-tight text-paper"
            >
              The one thing<br />
              LeetCode<br />
              can't{' '}
              <span className="text-ember">simulate.</span>
            </motion.h1>

            <motion.p variants={fadeUp} className="mt-8 max-w-md text-base leading-relaxed text-paper-dim">
            Realistic SWE mock interviews with a live AI Interviewer. Practice coding, behavioral, or both. Adaptive follow-up questions, real pressure, clear evidence-based feedback.
            </motion.p>

            <motion.div variants={fadeUp} className="mt-10 flex flex-wrap items-center gap-4">
              <button
                onClick={() => navigate('/setup')}
                className="group flex items-center gap-3 rounded-sm bg-ember px-6 py-3 font-mono text-sm font-medium uppercase tracking-widest text-ink-950 transition-all duration-200 hover:bg-ember-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-ember focus-visible:outline-offset-2 active:scale-[0.97]"
              >
                Begin a session
                <span className="transition-transform duration-200 group-hover:translate-x-1">→</span>
              </button>
              <button
                onClick={() => navigate('/feedback/feedback-1')}
                className="font-mono text-sm uppercase tracking-widest text-paper-dim transition-colors duration-200 hover:text-paper border-b border-transparent hover:border-paper-faint pb-px"
              >
                See sample feedback
              </button>
            </motion.div>

            <motion.div variants={fadeUp} className="mt-12 flex items-center gap-6">
              {['Voice AI', 'Monaco editor', 'Company-specific'].map((tag) => (
                <div key={tag} className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-ember" />
                  <span className="font-mono text-xs text-paper-faint">{tag}</span>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Right: transcript card */}
          <motion.div variants={fadeUp} className="flex items-center justify-center">
            <div className="w-full max-w-md rounded-md border border-ink-700/80 bg-ink-900 p-6 shadow-card">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 animate-pulse-ember rounded-full bg-ember" />
                  <span className="font-mono text-xs text-ember">Live session</span>
                </div>
                <span className="font-mono text-xs text-paper-faint">00:12:43</span>
              </div>

              <div className="mb-4 rounded-sm border border-ink-700/50 bg-ink-800 px-3 py-2">
                <p className="font-mono text-xs text-paper-faint">Two Sum — Easy</p>
              </div>

              <div className="space-y-3">
                {sampleTranscript.map((line, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + i * 0.18, duration: 0.35 }}
                    className="flex gap-3"
                  >
                    <span className={`mt-0.5 shrink-0 font-mono text-[10px] font-medium ${line.speaker === 'I' ? 'text-paper-faint' : 'text-ember'}`}>
                      {line.speaker === 'I' ? 'INT' : 'YOU'}
                    </span>
                    <p className={`text-sm leading-relaxed ${line.highlight ? 'text-paper' : 'text-paper-dim'}`}>
                      {line.highlight && (
                        <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-ember align-middle" />
                      )}
                      {line.text}
                    </p>
                  </motion.div>
                ))}
              </div>

              <div className="mt-5 border-t border-ink-700/50 pt-4">
                <p className="font-mono text-[10px] uppercase tracking-widest text-paper-faint">
                  Clarity <span className="text-ember">82</span> · Confidence <span className="text-ember">71</span> · Technical <span className="text-ember">79</span>
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Browser scroll reveal */}
      <BrowserScrollReveal />

      {/* Feature strip */}
      <section className="relative border-t border-ink-700/40 bg-ink-900/40 py-20">
        <div className="mx-auto max-w-7xl px-6">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-80px' }}
            className="grid grid-cols-1 gap-6 md:grid-cols-3 md:items-stretch"
          >
            {features.map(({ num, title, body }) => (
              <motion.div key={num} variants={fadeUp} className="flex">
                <LiquidGlass className="p-8 flex-1">
                  <p className="mb-4 font-mono text-xs tracking-widest text-ember">{num}</p>
                  <h3 className="mb-3 font-sans text-xl font-bold text-paper">{title}</h3>
                  <p className="text-sm leading-relaxed text-paper-dim">{body}</p>
                </LiquidGlass>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Social proof — company strip */}
      <section className="py-16">
        <div className="mx-auto max-w-7xl px-6">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <p className="mb-8 text-center font-mono text-xs uppercase tracking-widest text-paper-faint">
              Practice for interviews at
            </p>
            <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
              {companies.map((co) => (
                <span
                  key={co}
                  className="font-sans text-lg font-semibold text-paper-faint/40 transition-colors duration-200 hover:text-paper-dim"
                >
                  {co}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="relative border-t border-ink-700/40 py-24">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute bottom-0 left-1/2 h-[300px] w-[600px] -translate-x-1/2 rounded-full bg-ember/3 blur-[100px]" />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55 }}
          className="mx-auto max-w-2xl px-6 text-center"
        >
          <h2 className="mb-4 font-sans text-4xl font-extrabold text-paper md:text-5xl">
            Ready to run a mock interview?
          </h2>
          <p className="mb-8 text-paper-dim">Set up your session in 60 seconds. No account required.</p>
          <button
            onClick={() => navigate('/setup')}
            className="group inline-flex items-center gap-3 rounded-sm bg-ember px-8 py-4 font-mono text-sm font-medium uppercase tracking-widest text-ink-950 transition-all duration-200 hover:bg-ember-soft active:scale-[0.97]"
          >
            Start practicing now
            <span className="transition-transform duration-200 group-hover:translate-x-1">→</span>
          </button>
        </motion.div>
      </section>
    </div>
  )
}
