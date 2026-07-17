'use client';

import Link from 'next/link';
import {useState} from 'react';
import {BrandLogo} from './BrandLogo';
import {PricingSection} from './PricingSection';
import {LanguageSelector} from './LocaleProvider';
import {publicFaqs} from '../lib/seo-content';
import baseStyles from './LandingPage.module.css';
import conversionStyles from './LandingConversion.module.css';
import faqStyles from './LandingFaq.module.css';

const styles = {...baseStyles, ...conversionStyles, ...faqStyles};
const signals = {
  act: {label: 'Act', title: 'Blind-box collection reveals', score: 'TOS 84', confidence: '● High', velocity: '18.6k/hour', note: 'Eight unrelated creators adopted the mechanism while velocity continued to rise.', safety: '✓ Clear'},
  monitor: {label: 'Monitor', title: 'Screen-free travel activity kits', score: 'TOS 68', confidence: '◐ Medium', velocity: '6.3k/hour', note: 'The consumer need is clear, but only four independent creators are represented.', safety: '✓ Clear'},
  avoid: {label: 'Avoid', title: 'Microwaved sensory-gel challenge', score: 'TOS 31', confidence: '● High', velocity: '21.1k/hour', note: 'Real momentum does not override product-misuse and safety risk.', safety: '! Safety hold'},
};

export function LandingPage() {
  const [mode, setMode] = useState<keyof typeof signals>('act');
  const signal = signals[mode];
  return <div className={styles.site}>
    <header className={styles.header}>
      <Link className={styles.logo} href="/" aria-label="SignalScope home"><BrandLogo variant="on-dark" priority sizes="(max-width: 560px) 165px, 190px"/></Link>
      <nav aria-label="Primary navigation"><a href="#problem">Problem</a><a href="#workflow">Workflow</a><a href="#trust">Methodology</a><a href="#pricing">Pricing</a><Link href="/dashboard">Demo</Link></nav>
      <LanguageSelector compact/>
      <Link className={styles.headerCta} href="/dashboard">Explore product demo</Link>
    </header>
    <main>
      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className={styles.kicker}>Short-form trend decision intelligence for professional teams</p>
          <h1>Know what is gaining momentum—<em>and what your team should do next.</em></h1>
          <p className={styles.lead}>SignalScope turns fragmented short-form social observations into evidence-backed Act, Monitor or Avoid decisions, original creative opportunities and stakeholder-ready reports.</p>
          <div className={styles.ctas}><Link className={styles.primary} href="/dashboard">Explore the toys demo <span>→</span></Link><Link className={styles.secondary} href="/discover">Inspect a signal</Link></div>
          <div className={styles.heroProof}><span>Social & influencer agencies</span><span>Multi-brand consumer teams</span><span>Retail & social commerce</span></div>
          <p className={styles.disclosure}><b>CURRENT DEMO CATEGORY: TOYS.</b> The working dashboard uses synthetic toy data to demonstrate the workflow. Additional categories are planned, not currently available.</p>
        </div>
        <div className={styles.heroVisual} aria-label="Illustrative trend decision brief using the current toys demo">
          <div className={styles.visualHead}><span>Current demo · Toys & family · GB</span><b>SYNTHETIC DATA</b></div>
          <div className={styles.watchRow}><span>CATEGORY WATCHLIST</span><b>What changed since review</b><small>Toys demo</small></div>
          <div className={styles.miniDecisions}><span className={styles.active}>Act <b>03</b></span><span>Monitor <b>05</b></span><span>Avoid <b>03</b></span></div>
          <div className={styles.heroSignal}><small>ACCELERATING · ILLUSTRATIVE SIGNAL</small><h2>Blind-box collection reveals</h2><p>Adoption across eight unrelated creators</p><div className={styles.chart}>{[16, 23, 21, 32, 45, 58, 76, 91].map((height, index) => <i key={index} style={{height: `${height}%`}}/>)}</div><footer><b>TOS 84</b><span>● High confidence</span><span>18.6k views/hour</span></footer></div>
          <aside>Decision context <p>Test a differentiated reveal structure within 72 hours. Do not copy creator wording, staging or licensed expression.</p></aside>
        </div>
      </section>

      <section className={styles.recognition} id="problem">
        <div className={styles.sectionIntro}><p className={styles.kicker}>The problem it solves</p><h2>Trends move faster than the research process around them.</h2><p>Social, creative and insights teams save disconnected examples, compare view counts by instinct and rebuild the same evidence for every client, brand and category.</p></div>
        <div className={styles.painGrid}>{[
          ['Late decisions', 'The useful testing window closes while teams debate whether a pattern is relevant or repeatable.'],
          ['Views without context', 'Reach alone cannot show acceleration, creator spread, saturation, confidence or evidence gaps.'],
          ['Risky inspiration', 'Popular content can still create brand-safety, product, rights or reputational risk.'],
          ['Client-ready proof', 'Stakeholders need a defensible recommendation, not another folder of screenshots and links.'],
        ].map(([title, body], index) => <article key={title}><span>0{index + 1}</span><h3>{title}</h3><p>{body}</p></article>)}</div>
      </section>

      <section className={styles.workflow} id="workflow">
        <div className={styles.sectionIntro}><p className={styles.kicker}>One repeatable decision workflow</p><h2>Detect. Explain. Decide. Brief. Report.</h2></div>
        <ol>{[
          ['Detect momentum', 'Monitor relevant posts through chosen categories, keywords, hashtags and selected public profiles.'],
          ['Preserve evidence', 'Append repeated observations instead of replacing earlier metrics with the latest number.'],
          ['Explain movement', 'Review velocity, acceleration, creator spread, freshness, saturation and limitations.'],
          ['Make a decision', 'Record Act, Monitor or Avoid with a reason, owner and decision window.'],
          ['Create original work', 'Turn the repeatable mechanism into a responsible brief and source-linked report.'],
        ].map(([title, body], index) => <li key={title}><span>0{index + 1}</span><div><h3>{title}</h3><p>{body}</p></div></li>)}</ol>
        <Link className={styles.textLink} href="/dashboard">Open the current product demo →</Link>
      </section>

      <section className={styles.preview} aria-labelledby="preview-title">
        <div className={styles.sectionIntro}><p className={styles.kicker}>Decision before vanity metrics</p><h2 id="preview-title">The same reach can lead to three different decisions.</h2></div>
        <div className={styles.switcher} role="group" aria-label="Illustrative decision"><button aria-pressed={mode === 'act'} onClick={() => setMode('act')}>Act</button><button aria-pressed={mode === 'monitor'} onClick={() => setMode('monitor')}>Monitor</button><button aria-pressed={mode === 'avoid'} onClick={() => setMode('avoid')}>Avoid</button></div>
        <article className={`${styles.signalCard} ${styles[mode]}`}><header><div><small>{signal.label.toUpperCase()}</small><h3>{signal.title}</h3><p>Current toys demo · synthetic GB/PL sample</p></div><span>{signal.safety}</span></header><div className={styles.signalStats}><span><b>{signal.score}</b>Category opportunity score</span><span><b>{signal.confidence}</b>Evidence quality</span><span><b>{signal.velocity}</b>Observed velocity</span><div className={styles.sparkline}>{[18, 20, 27, 25, 39, 51, 68, 82].map((height, index) => <i key={index} style={{height: `${height}%`}}/>)}</div></div><aside><b>Why it matters</b><p>{signal.note}</p></aside></article>
        <Link className={styles.textLink} href="/discover">Inspect signal evidence →</Link>
      </section>

      <section className={styles.solutions}>
        <div className={styles.sectionIntro}><p className={styles.kicker}>Built for the teams making high-frequency social decisions</p><h2>One evidence base for agency, brand and commerce workflows.</h2></div>
        <div className={styles.roleLayout}>
          <div className={styles.roleTabs}>{['Agencies', 'Consumer brands', 'Retail & commerce', 'Media & lifestyle'].map((item) => <span key={item}>{item}</span>)}</div>
          <article className={styles.rolePanel}><small>FOR SOCIAL, CREATIVE, INFLUENCER AND INSIGHTS LEADERS</small><h3>Move from cultural movement to a decision your team can defend.</h3><p>Agencies compare opportunities across client briefs. Multi-brand companies monitor category priorities. Retail and social-commerce teams connect momentum to trading moments. Entertainment, gaming, beauty, fashion and lifestyle teams translate signals into original creative action.</p><b>Less manual research, clearer prioritisation and limitations attached to every recommendation.</b><Link href="/reports">View the current demo report →</Link></article>
        </div>
      </section>

      <section className={styles.trust} id="trust">
        <div><p className={styles.kicker}>Evidence before excitement</p><h2>Every recommendation should show its workings.</h2><p>SignalScope does not predict virality. It distinguishes unavailable metrics from zero, separates observed evidence from interpretation and keeps provider and coverage limitations visible.</p><div className={styles.trustLinks}><Link href="/workspace?tab=methodology">Methodology</Link><Link href="/workspace?tab=data-health">Data health</Link><Link href="/legal/privacy">Privacy</Link><Link href="/legal/ai-disclosure">AI disclosure</Link></div></div>
        <ul><li><b>Repeated observations</b><span>Velocity requires two snapshots; acceleration requires three.</span></li><li><b>Confidence attached</b><span>Completeness, creator spread, freshness and provider health support confidence.</span></li><li><b>Category-aware review</b><span>Safety, claims, licensed expression, music rights and brand suitability remain visible.</span></li><li><b>Independent product</b><span>SignalScope is not affiliated with TikTok or ByteDance.</span></li></ul>
      </section>

      <section className={styles.report}><div><p className={styles.kicker}>For the next stakeholder conversation</p><h2>Turn observed signals into a decision-ready brief.</h2><p>Lead with Act, Monitor and Avoid, then show category, creator, hashtag, sound, safety, confidence and evidence context.</p><Link className={styles.secondary} href="/reports">View demo report</Link></div><div className={styles.reportSheet}><header>Trend decision brief <span>TOYS DEMO</span></header>{['Executive summary', 'Act now', 'Monitor', 'Avoid or hold', 'Evidence and limitations'].map((item, index) => <p key={item}><b>0{index + 1}</b>{item}</p>)}<footer>Decision view · Excel · HTML · CSV</footer></div></section>

      <section className={styles.faq}><div className={styles.sectionIntro}><p className={styles.kicker}>Before using the evidence</p><h2>Buyer questions about coverage, categories and workflow.</h2><p>The current working product demonstration uses synthetic toy data. Other categories are planned and should not be treated as available until their data and workflows are implemented.</p></div><div className={styles.faqList}>{publicFaqs.map((item) => <details key={item.question}><summary>{item.question}</summary><p>{item.answer}</p></details>)}</div></section>
      <PricingSection/>
      <section className={styles.final}><p className={styles.kicker}>Evaluate the workflow</p><h2>See whether SignalScope makes trend decisions easier to defend.</h2><p>Explore the current toys demonstration, inspect the evidence and build an original brief.</p><div className={styles.ctas}><Link className={styles.primary} href="/dashboard">Explore product demo →</Link><Link className={styles.secondary} href="/discover">Inspect a signal</Link></div><small>CURRENT DEMO: TOYS · Synthetic data · More categories coming soon.</small></section>
    </main>
  </div>;
}
