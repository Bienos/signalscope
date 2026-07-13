'use client';

import Image from 'next/image';
import Link from 'next/link';
import {useState} from 'react';
import {PricingSection} from './PricingSection';
import {LanguageSelector} from './LocaleProvider';
import {publicFaqs} from '../lib/seo-content';
import baseStyles from './LandingPage.module.css';
import conversionStyles from './LandingConversion.module.css';
import faqStyles from './LandingFaq.module.css';

const styles = {...baseStyles, ...conversionStyles, ...faqStyles};
const signals = {
  act: {label: 'Act', title: 'Blind-box collection reveals', score: 'TOS 84', confidence: '● High', velocity: '18.6k/hour', note: 'Eight unrelated toy creators adopted the mechanism while velocity continued to rise.', safety: '✓ Clear'},
  monitor: {label: 'Monitor', title: 'Screen-free travel activity kits', score: 'TOS 68', confidence: '◐ Medium', velocity: '6.3k/hour', note: 'The parent need is clear, but only four independent creators are represented.', safety: '✓ Clear'},
  avoid: {label: 'Avoid', title: 'Microwaved sensory-gel challenge', score: 'TOS 31', confidence: '● High', velocity: '21.1k/hour', note: 'Real momentum does not override heating and product-misuse risk.', safety: '! Safety hold'},
};

export function LandingPage() {
  const [mode, setMode] = useState<keyof typeof signals>('act');
  const signal = signals[mode];
  return <div className={styles.site}>
    <header className={styles.header}>
      <Link className={styles.logo} href="/" aria-label="SignalScope home"><Image src="/brand/signalscope-horizontal-dark.png" width={190} height={55} alt="SignalScope" priority/></Link>
      <nav aria-label="Primary navigation"><a href="#problem">Problem</a><a href="#workflow">Workflow</a><a href="#trust">Methodology</a><a href="#pricing">Pricing</a><Link href="/dashboard">Demo</Link></nav>
      <LanguageSelector compact/>
      <Link className={styles.headerCta} href="/dashboard">Explore toy demo</Link>
    </header>
    <main>
      <section className={styles.hero}>
        <div className={styles.heroCopy}><p className={styles.kicker}>Toy trend intelligence for brands, retailers and agencies</p><h1>Know what is moving in toys—<em>and what your team should test next.</em></h1><p className={styles.lead}>SignalScope turns repeated TikTok observations into evidence-backed toy signals, clear Act, Monitor or Avoid decisions, and original creative briefs.</p><div className={styles.ctas}><Link className={styles.primary} href="/dashboard">Explore demo toy data <span>→</span></Link><Link className={styles.secondary} href="/discover">Inspect a toy signal</Link></div><div className={styles.heroProof}><span>Toy brands</span><span>Toy retailers</span><span>Social & influencer agencies</span></div><p className={styles.disclosure}><b>DEMO TOY DATA.</b> Synthetic provider fixtures illustrate the workflow. Coverage is a configured sample, not a complete TikTok ranking.</p></div>
        <div className={styles.heroVisual} aria-label="Illustrative toy trend decision brief"><div className={styles.visualHead}><span>Blind boxes & collectibles · GB</span><b>DEMO TOY DATA</b></div><div className={styles.watchRow}><span>TOY WATCHLIST</span><b>What changed since review</b><small>Synthetic</small></div><div className={styles.miniDecisions}><span className={styles.active}>Act <b>03</b></span><span>Monitor <b>05</b></span><span>Avoid <b>03</b></span></div><div className={styles.heroSignal}><small>ACCELERATING · SYNTHETIC SIGNAL</small><h2>Blind-box collection reveals</h2><p>Adoption across eight unrelated toy creators</p><div className={styles.chart}>{[16, 23, 21, 32, 45, 58, 76, 91].map((height, index) => <i key={index} style={{height: `${height}%`}}/>)}</div><footer><b>TOS 84</b><span>● High confidence</span><span>18.6k views/hour</span></footer></div><aside>Decision context <p>Test a differentiated reveal structure within 72 hours. Do not copy creator wording, staging or licensed expression.</p></aside></div>
      </section>

      <section className={styles.recognition} id="problem"><div className={styles.sectionIntro}><p className={styles.kicker}>The problem it solves</p><h2>Toy trends move faster than the research process around them.</h2><p>Teams save disconnected examples, compare view counts by instinct and rebuild the same evidence for every client or category.</p></div><div className={styles.painGrid}>{[
        ['Late decisions', 'The useful testing window closes while teams debate whether a toy pattern is real.'],
        ['Views without context', 'Reach alone cannot show acceleration, creator spread, saturation or evidence gaps.'],
        ['Unsafe inspiration', 'A popular challenge can still create product-safety, child-privacy or rights risk.'],
        ['Client-ready proof', 'Agencies need a defensible recommendation, not another folder of screenshots.'],
      ].map(([title, body], index) => <article key={title}><span>0{index + 1}</span><h3>{title}</h3><p>{body}</p></article>)}</div></section>

      <section className={styles.workflow} id="workflow"><div className={styles.sectionIntro}><p className={styles.kicker}>One toy-market decision workflow</p><h2>Detect. Explain. Decide. Brief. Report.</h2></div><ol>{[
        ['Detect momentum', 'Discover toy posts by keyword, hashtag and selected public profiles.'],
        ['Preserve evidence', 'Append repeated observations instead of overwriting earlier metrics.'],
        ['Explain movement', 'Review velocity, acceleration, creator spread, freshness and saturation.'],
        ['Make a decision', 'Persist Act, Monitor or Avoid with a reason and review window.'],
        ['Create original work', 'Turn the mechanism into a safe, source-linked brief and report.'],
      ].map(([title, body], index) => <li key={title}><span>0{index + 1}</span><div><h3>{title}</h3><p>{body}</p></div></li>)}</ol><Link className={styles.textLink} href="/dashboard">Open today&apos;s toy brief →</Link></section>

      <section className={styles.preview} aria-labelledby="preview-title"><div className={styles.sectionIntro}><p className={styles.kicker}>Decision before vanity metrics</p><h2 id="preview-title">The same reach can lead to three different decisions.</h2></div><div className={styles.switcher} role="group" aria-label="Illustrative decision"><button aria-pressed={mode === 'act'} onClick={() => setMode('act')}>Act</button><button aria-pressed={mode === 'monitor'} onClick={() => setMode('monitor')}>Monitor</button><button aria-pressed={mode === 'avoid'} onClick={() => setMode('avoid')}>Avoid</button></div><article className={`${styles.signalCard} ${styles[mode]}`}><header><div><small>{signal.label.toUpperCase()}</small><h3>{signal.title}</h3><p>Synthetic toy signal · configured GB/PL sample</p></div><span>{signal.safety}</span></header><div className={styles.signalStats}><span><b>{signal.score}</b>Toy opportunity score</span><span><b>{signal.confidence}</b>Evidence quality</span><span><b>{signal.velocity}</b>Observed velocity</span><div className={styles.sparkline}>{[18, 20, 27, 25, 39, 51, 68, 82].map((height, index) => <i key={index} style={{height: `${height}%`}}/>)}</div></div><aside><b>Why it matters</b><p>{signal.note}</p></aside></article><Link className={styles.textLink} href="/discover">Inspect signal evidence →</Link></section>

      <section className={styles.solutions}><div className={styles.sectionIntro}><p className={styles.kicker}>Built for the people making toy-market decisions</p><h2>One evidence base, three commercial workflows.</h2></div><div className={styles.roleLayout}><div className={styles.roleTabs}>{['Toy brands', 'Toy retailers', 'Agencies'].map((item) => <span key={item}>{item}</span>)}</div><article className={styles.rolePanel}><small>TOY-SPECIFIC INTELLIGENCE</small><h3>Move from cultural movement to a defensible test.</h3><p>Brand social teams prioritise content, retail teams connect category momentum to trading moments, and agencies turn repeatable research into stronger client recommendations.</p><b>Faster decisions with confidence, freshness and limitations attached.</b><Link href="/reports">View a decision report →</Link></article></div></section>

      <section className={styles.trust} id="trust"><div><p className={styles.kicker}>Evidence before excitement</p><h2>A toy recommendation should show its workings.</h2><p>SignalScope does not predict virality. It distinguishes unavailable metrics from zero, separates popularity from safety and keeps provider and coverage limitations visible.</p><div className={styles.trustLinks}><Link href="/workspace?tab=methodology">Methodology</Link><Link href="/workspace?tab=data-health">Data health</Link><Link href="/legal/privacy">Privacy</Link><Link href="/legal/ai-disclosure">AI disclosure</Link></div></div><ul><li><b>Repeated observations</b><span>Velocity requires two snapshots; acceleration requires three.</span></li><li><b>Confidence attached</b><span>Completeness, creator spread, freshness and provider health support confidence.</span></li><li><b>Toy-specific risk</b><span>Safety, product claims, licensed characters, music rights and child privacy remain visible.</span></li><li><b>Independent product</b><span>SignalScope is not affiliated with TikTok or ByteDance.</span></li></ul></section>

      <section className={styles.report}><div><p className={styles.kicker}>For the next stakeholder conversation</p><h2>Turn today&apos;s toy signals into a client-ready decision brief.</h2><p>Lead with Act, Monitor and Avoid, then show the category, creator, hashtag, sound, safety and evidence context.</p><Link className={styles.secondary} href="/reports">View demo report</Link></div><div className={styles.reportSheet}><header>Toy trend decision brief <span>DEMO</span></header>{['Executive summary', 'Act now', 'Monitor', 'Avoid or hold', 'Evidence and limitations'].map((item, index) => <p key={item}><b>0{index + 1}</b>{item}</p>)}<footer>Decision view · Excel · HTML · CSV</footer></div></section>
      <section className={styles.faq}><div className={styles.sectionIntro}><p className={styles.kicker}>Before using the evidence</p><h2>Buyer questions about coverage, safety and workflow.</h2><p>The current public experience is a synthetic toy-data demonstration. Live collection remains disabled until an authorised provider is configured.</p></div><div className={styles.faqList}>{publicFaqs.map((item) => <details key={item.question}><summary>{item.question}</summary><p>{item.answer}</p></details>)}</div></section>
      <PricingSection/>
      <section className={styles.final}><p className={styles.kicker}>Evaluate the workflow</p><h2>See whether SignalScope makes toy trend decisions easier to defend.</h2><p>Explore synthetic toy signals, inspect the evidence and build an original brief.</p><div className={styles.ctas}><Link className={styles.primary} href="/dashboard">Explore demo toy data →</Link><Link className={styles.secondary} href="/discover">Inspect a signal</Link></div><small>DEMO TOY DATA · Live monitoring and automatic alerts are not enabled.</small></section>
    </main>
  </div>;
}
