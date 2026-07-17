'use client';

import Link from 'next/link';
import {useState} from 'react';
import {publicFaqs} from '../lib/seo-content';
import {BrandLogo} from './BrandLogo';
import {PricingSection} from './PricingSection';
import baseStyles from './LandingPage.module.css';
import conversionStyles from './LandingConversion.module.css';
import faqStyles from './LandingFaq.module.css';

const styles = [baseStyles, conversionStyles, faqStyles].reduce<Record<string, string>>((combined, stylesheet) => {
  Object.entries(stylesheet).forEach(([name, className]) => {
    combined[name] = [combined[name], className].filter(Boolean).join(' ');
  });
  return combined;
}, {});

type Decision = 'act' | 'monitor' | 'avoid';

const signals: Record<Decision, {
  label: string;
  eyebrow: string;
  title: string;
  score: string;
  confidence: string;
  freshness: string;
  velocity: string;
  creators: string;
  evidence: string;
  action: string;
  safety: string;
}> = {
  act: {
    label: 'Act',
    eyebrow: 'Accelerating mechanism',
    title: 'Blind-box collection reveals',
    score: 'TOS 84',
    confidence: 'High',
    freshness: '38 min ago',
    velocity: '18.6k / hour',
    creators: '8 independent creators',
    evidence: 'Creator adoption broadened while observed velocity continued to rise across the monitored sample.',
    action: 'Brief a differentiated reveal concept for client review within 72 hours.',
    safety: 'No current safety hold',
  },
  monitor: {
    label: 'Monitor',
    eyebrow: 'Promising, limited evidence',
    title: 'Screen-free travel activity kits',
    score: 'TOS 68',
    confidence: 'Medium',
    freshness: '1 hr ago',
    velocity: '6.3k / hour',
    creators: '4 independent creators',
    evidence: 'The consumer need is relevant, but the monitored sample is still concentrated among too few creators.',
    action: 'Recheck creator spread and acceleration at the next scheduled review.',
    safety: 'No current safety hold',
  },
  avoid: {
    label: 'Avoid',
    eyebrow: 'Momentum with material risk',
    title: 'Microwaved sensory-gel challenge',
    score: 'TOS 31',
    confidence: 'High',
    freshness: '24 min ago',
    velocity: '21.1k / hour',
    creators: '11 independent creators',
    evidence: 'Observed reach is high, but the mechanism introduces product-misuse and safety concerns.',
    action: 'Do not adapt. Record the risk and monitor for adjacent, safer mechanisms.',
    safety: 'Safety hold',
  },
};

const proofItems = [
  'Built for multi-client research',
  'Evidence attached to every recommendation',
  'Act · Monitor · Avoid',
  'Client-ready reporting',
];

const decisionOrder: Decision[] = ['act', 'monitor', 'avoid'];

const workflow = [
  ['Detect', 'Surface category-relevant momentum from a configured monitored sample.'],
  ['Explain', 'Inspect velocity, acceleration, creator adoption, freshness and evidence gaps.'],
  ['Decide', 'Record Act, Monitor or Avoid with a reason and a practical decision window.'],
  ['Deliver', 'Turn approved opportunities into original briefs and source-linked reports.'],
];

const useCases = [
  ['Social strategy', 'Prioritise what deserves attention across client categories without rebuilding the research method each time.'],
  ['Creative strategy', 'Separate a repeatable mechanism from a creator\'s protected expression before writing an original brief.'],
  ['Consumer insights', 'Give stakeholders an evidence trail with freshness, confidence, provenance and known limitations.'],
  ['Influencer teams', 'Review creator adoption and momentum in context instead of treating follower count as the decision.'],
  ['Social commerce', 'Connect category movement to a practical testing window while keeping product and safety risks visible.'],
  ['Leadership', 'Share a concise decision view that explains what changed, why it matters and what happens next.'],
];

export function LandingPage() {
  const [mode, setMode] = useState<Decision>('act');
  const [menuOpen, setMenuOpen] = useState(false);
  const signal = signals[mode];

  const closeMenu = () => setMenuOpen(false);

  return <div className={styles.site}>
    <a className={styles.skipLink} href="#main-content">Skip to content</a>
    <header className={styles.header} onKeyDown={(event) => {
      if (event.key === 'Escape') setMenuOpen(false);
    }}>
      <div className={styles.headerInner}>
        <Link className={styles.logo} href="/" aria-label="SignalScope home" onClick={closeMenu}>
          <BrandLogo variant="on-dark" priority sizes="(max-width: 560px) 166px, 190px"/>
        </Link>
        <button
          className={styles.menuButton}
          type="button"
          aria-expanded={menuOpen}
          aria-controls="homepage-navigation"
          aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span/><span/><span/>
        </button>
        <nav id="homepage-navigation" className={`${styles.navigation} ${menuOpen ? styles.menuOpen : ''}`} aria-label="Primary navigation">
          <a href="#product" onClick={closeMenu}>Product</a>
          <a href="#solutions" onClick={closeMenu}>Solutions</a>
          <a href="#methodology" onClick={closeMenu}>Methodology</a>
          <a href="#pricing" onClick={closeMenu}>Pricing</a>
          <Link className={styles.signIn} href="/login" onClick={closeMenu}>Sign in</Link>
          <Link className={styles.headerCta} href="/dashboard" onClick={closeMenu}>See this week&apos;s signals</Link>
        </nav>
      </div>
    </header>

    <main id="main-content">
      <section className={styles.hero} id="product">
        <div className={styles.heroCopy}>
          <p className={styles.kicker}>Short-form intelligence for agencies and consumer teams</p>
          <h1>Turn emerging short-form signals into <em>client-ready decisions.</em></h1>
          <p className={styles.lead}>SignalScope helps teams identify what is gaining momentum, understand the evidence behind it and turn the strongest opportunities into watchlists, briefs and reports before the decision window closes.</p>
          <div className={styles.ctas}>
            <Link className={styles.primary} href="/dashboard">See this week&apos;s signals <span aria-hidden="true">→</span></Link>
            <Link className={styles.secondary} href="/reports">View a sample report</Link>
          </div>
          <p className={styles.disclosure}><b>Current product preview: toys and family.</b> The working dashboard uses simulated provider data to demonstrate the decision workflow. Additional categories are planned, not currently available.</p>
        </div>

        <div className={styles.heroVisual} aria-label="Illustrative SignalScope client watchlist using simulated toy data">
          <div className={styles.visualHead}>
            <div><span>Client watchlist</span><b>Toys &amp; family · UK</b></div>
            <div><span>Freshness</span><b>Updated 07:42</b></div>
          </div>
          <div className={styles.previewDisclosure}><span>Simulated data</span><span>Configured sample</span><span>Not a complete ranking</span></div>
          <div className={styles.visualSummary}>
            <div><small>Priority signal</small><h2>Blind-box collection reveals</h2><p>Adoption broadened across unrelated creators while momentum continued to rise.</p></div>
            <span className={styles.actBadge}>Act</span>
          </div>
          <div className={styles.visualMetrics}>
            <span><small>Opportunity</small><b>TOS 84</b></span>
            <span><small>Confidence</small><b>High</b></span>
            <span><small>Velocity</small><b>18.6k/h</b></span>
            <span><small>Creators</small><b>8</b></span>
          </div>
          <div className={styles.chartBlock}>
            <div><span>Observed momentum</span><small>Repeated snapshots</small></div>
            <div className={styles.lineChart} aria-hidden="true">
              <svg viewBox="0 0 560 144" preserveAspectRatio="none">
                <path className={styles.gridLine} d="M0 28H560M0 72H560M0 116H560"/>
                <path className={styles.areaLine} d="M0 122 C70 120 86 109 126 112 S198 102 238 91 S300 86 346 69 S414 55 456 37 S520 28 560 14 L560 144 L0 144 Z"/>
                <path className={styles.dataLine} d="M0 122 C70 120 86 109 126 112 S198 102 238 91 S300 86 346 69 S414 55 456 37 S520 28 560 14"/>
              </svg>
            </div>
          </div>
          <div className={styles.nextAction}><span>Recommended next action</span><p>Brief a differentiated reveal concept for client review within 72 hours.</p></div>
        </div>
      </section>

      <section className={styles.proofStrip} aria-label="Product value summary">
        {proofItems.map((item) => <span key={item}>{item}</span>)}
      </section>

      <section className={styles.recognition} id="problem">
        <div className={styles.sectionIntro}>
          <p className={styles.kicker}>The operational problem</p>
          <h2>Your team is not short of trends. It is short of defensible decisions.</h2>
          <p>Agency and brand teams repeatedly collect links, compare screenshots and reformat the same research while the useful approval window gets smaller.</p>
        </div>
        <div className={styles.painGrid}>
          <article><span>01</span><h3>Research repeats across clients</h3><p>Useful observations are scattered across feeds, messages and spreadsheets instead of one consistent review method.</p></article>
          <article><span>02</span><h3>Reach is mistaken for relevance</h3><p>High views do not explain acceleration, creator spread, saturation, safety or the quality of the evidence.</p></article>
          <article><span>03</span><h3>Recommendations arrive too late</h3><p>By the time evidence is collected, formatted and approved, the practical testing window may have closed.</p></article>
          <article><span>04</span><h3>Stakeholders need a rationale</h3><p>Clients and leaders need to know what changed, why it matters and what the team should do—not another folder of examples.</p></article>
        </div>
      </section>

      <section className={styles.workflow} id="workflow">
        <div className={styles.sectionIntro}>
          <p className={styles.kicker}>A repeatable decision system</p>
          <h2>Detect → Explain → Decide → Deliver</h2>
          <p>SignalScope structures the work around a decision, while strategists retain responsibility for context, originality and judgement.</p>
        </div>
        <ol>{workflow.map(([title, body], index) => <li key={title}><span>0{index + 1}</span><div><h3>{title}</h3><p>{body}</p></div></li>)}</ol>
      </section>

      <section className={styles.preview} aria-labelledby="decision-example-title">
        <div className={styles.sectionIntro}>
          <p className={styles.kicker}>Interactive evidence example</p>
          <h2 id="decision-example-title">Momentum is evidence—not the decision.</h2>
          <p>Compare how evidence quality, risk and timing change the recommended response.</p>
        </div>
        <div className={styles.switcher} role="tablist" aria-label="Illustrative signal decision">
          {decisionOrder.map((item) => <button
            key={item}
            id={`decision-tab-${item}`}
            role="tab"
            type="button"
            aria-selected={mode === item}
            aria-controls={`decision-panel-${item}`}
            tabIndex={mode === item ? 0 : -1}
            onClick={() => setMode(item)}
            onKeyDown={(event) => {
              const currentIndex = decisionOrder.indexOf(item);
              let nextIndex = currentIndex;
              if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % decisionOrder.length;
              else if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + decisionOrder.length) % decisionOrder.length;
              else if (event.key === 'Home') nextIndex = 0;
              else if (event.key === 'End') nextIndex = decisionOrder.length - 1;
              else return;
              event.preventDefault();
              const next = decisionOrder[nextIndex];
              setMode(next);
              event.currentTarget.parentElement?.querySelector<HTMLButtonElement>(`#decision-tab-${next}`)?.focus();
            }}
          >{signals[item].label}</button>)}
        </div>
        <article
          className={`${styles.signalCard} ${styles[mode]}`}
          id={`decision-panel-${mode}`}
          role="tabpanel"
          aria-labelledby={`decision-tab-${mode}`}
          tabIndex={0}
        >
          <header><div><small>{signal.eyebrow}</small><h3>{signal.title}</h3><p>Current toys preview · simulated UK sample</p></div><span>{signal.label}</span></header>
          <div className={styles.signalStats}>
            <span><small>Opportunity</small><b>{signal.score}</b></span>
            <span><small>Confidence</small><b>{signal.confidence}</b></span>
            <span><small>Freshness</small><b>{signal.freshness}</b></span>
            <span><small>Velocity</small><b>{signal.velocity}</b></span>
            <span><small>Adoption</small><b>{signal.creators}</b></span>
            <span><small>Safety</small><b>{signal.safety}</b></span>
          </div>
          <div className={styles.decisionReason}><div><b>Observed evidence</b><p>{signal.evidence}</p></div><div><b>Recommended next action</b><p>{signal.action}</p></div></div>
        </article>
      </section>

      <section className={styles.agency} id="solutions">
        <div className={styles.agencyCopy}>
          <p className={styles.kicker}>Designed around agency reality</p>
          <h2>One research method across clients, categories and weekly reporting cycles.</h2>
          <p>SignalScope reduces collection, sorting and formatting work without replacing the strategist who understands the client, market and creative context.</p>
          <Link className={styles.textLink} href="/reports">See the report workflow <span aria-hidden="true">→</span></Link>
        </div>
        <div className={styles.agencyGrid}>
          <article><span>Client watchlists</span><p>Keep category, market and client questions separate while using one consistent evidence model.</p></article>
          <article><span>Weekly intelligence</span><p>Move from recurring research to a clear Act, Monitor and Avoid briefing structure.</p></article>
          <article><span>Defensible recommendations</span><p>Attach freshness, confidence, provenance, limitations and a decision window to the recommendation.</p></article>
          <article><span>Original creative briefs</span><p>Translate the repeatable mechanism into a distinct opportunity instead of copying a post.</p></article>
          <article><span>Stronger client conversations</span><p>Use evidence in pitches, retainers and planning meetings without overstating coverage or certainty.</p></article>
          <article><span>Less formatting work</span><p>Reuse a structured output across accounts while keeping human review and approval visible.</p></article>
        </div>
      </section>

      <section className={styles.useCases} aria-labelledby="use-cases-title">
        <div className={styles.sectionIntro}>
          <p className={styles.kicker}>Useful across the decision team</p>
          <h2 id="use-cases-title">A shared evidence base, shaped for each role.</h2>
        </div>
        <div className={styles.useCaseGrid}>{useCases.map(([title, body]) => <article key={title}><h3>{title}</h3><p>{body}</p></article>)}</div>
      </section>

      <section className={styles.report}>
        <div className={styles.reportCopy}>
          <p className={styles.kicker}>Client-ready deliverables</p>
          <h2>Move from observation to a report somebody can act on.</h2>
          <p>Lead with the decision, then show the evidence, confidence, freshness, risks and limitations that support it.</p>
          <ul><li>Executive summary by decision</li><li>Signal and creator evidence</li><li>Original opportunity and safety review</li><li>Sources, provenance and limitations</li></ul>
          <Link className={styles.secondary} href="/reports">View a sample report</Link>
        </div>
        <div className={styles.reportSheet} aria-label="Illustrative client trend decision report">
          <header><div><span>SignalScope</span><b>Weekly decision brief</b></div><small>Client category · 12 Jul 2026</small></header>
          <div className={styles.reportSummary}><span>Act <b>3</b></span><span>Monitor <b>5</b></span><span>Avoid <b>3</b></span></div>
          {['Executive decision summary', 'Priority opportunities', 'Signals to monitor', 'Risks and holds', 'Evidence and limitations'].map((item, index) => <p key={item}><b>0{index + 1}</b><span>{item}</span><i/></p>)}
          <footer>Decision view · Excel · HTML · CSV</footer>
        </div>
      </section>

      <section className={styles.methodology} id="methodology">
        <div className={styles.sectionIntro}>
          <p className={styles.kicker}>Methodology, confidence and provenance</p>
          <h2>Every recommendation should show its workings.</h2>
          <p>SignalScope organises permitted observations and interpretations. It does not predict virality, provide complete platform coverage or replace human strategic judgement.</p>
        </div>
        <div className={styles.methodGrid}>
          <article><span>01</span><h3>Observed evidence</h3><p>Repeated snapshots preserve movement over time. Missing metrics remain unavailable rather than becoming zero.</p></article>
          <article><span>02</span><h3>Confidence</h3><p>Evidence completeness, creator spread, freshness and provider health make uncertainty visible.</p></article>
          <article><span>03</span><h3>Interpretation</h3><p>Why-it-matters analysis and recommended actions remain clearly separate from observed facts.</p></article>
          <article><span>04</span><h3>Responsible action</h3><p>Originality, safety, rights and brand suitability checks stay connected to the opportunity.</p></article>
        </div>
        <div className={styles.trustLinks}><Link href="/legal/methodology">Methodology</Link><Link href="/legal/security">Security</Link><Link href="/legal/privacy">Privacy</Link><Link href="/legal/ai-disclosure">AI disclosure</Link></div>
        <p className={styles.independence}>SignalScope is an independent product and is not affiliated with TikTok or ByteDance.</p>
      </section>

      <section className={styles.comparison} aria-labelledby="comparison-title">
        <div className={styles.sectionIntro}>
          <p className={styles.kicker}>A focused operating layer</p>
          <h2 id="comparison-title">Built for the gap between finding a post and making a recommendation.</h2>
        </div>
        <div className={styles.tableWrap} role="region" aria-label="Research approach comparison" tabIndex={0}>
          <table>
            <caption>Comparison of common short-form research approaches</caption>
            <thead><tr><th scope="col">Capability</th><th scope="col">Manual research</th><th scope="col">Broad listening tools</th><th scope="col">SignalScope</th></tr></thead>
            <tbody>
              <tr><th scope="row">Category-relevant momentum</th><td>Collected manually</td><td>Often conversation-led</td><td>Structured signal review</td></tr>
              <tr><th scope="row">Freshness and confidence</th><td>Inconsistent</td><td>Varies by platform</td><td>Attached to the decision</td></tr>
              <tr><th scope="row">Act · Monitor · Avoid</th><td>Rebuilt per project</td><td>Not the core workflow</td><td>Central decision model</td></tr>
              <tr><th scope="row">Original opportunity brief</th><td>Separate task</td><td>Usually separate</td><td>Connected to evidence</td></tr>
              <tr><th scope="row">Client-ready report</th><td>Formatted manually</td><td>Dashboard export</td><td>Decision-led output</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <PricingSection/>

      <section className={styles.faq}>
        <div className={styles.sectionIntro}>
          <p className={styles.kicker}>Buyer questions</p>
          <h2>Coverage, categories and the decision workflow.</h2>
          <p>The current working product preview uses simulated toy data. Other categories are planned and should not be treated as available until their data and workflows are implemented.</p>
        </div>
        <div className={styles.faqList}>{publicFaqs.map((item) => <details key={item.question}><summary>{item.question}</summary><p>{item.answer}</p></details>)}</div>
      </section>

      <section className={styles.final}>
        <p className={styles.kicker}>A clearer answer for the next client meeting</p>
        <h2>See what changed, why it matters and what the team should do next.</h2>
        <p>Explore the current toys preview, inspect the evidence and see how a signal becomes a decision-ready report.</p>
        <div className={styles.ctas}><Link className={styles.primary} href="/dashboard">See this week&apos;s signals <span aria-hidden="true">→</span></Link><Link className={styles.secondary} href="/reports">View a sample report</Link></div>
        <small>Current preview: toys and family · Simulated data · Additional categories planned.</small>
      </section>
    </main>
    <footer className={styles.homeFooter}>
      <div className={styles.footerBrand}>
        <Link href="/" aria-label="SignalScope home"><BrandLogo variant="on-dark" sizes="210px"/></Link>
        <p>Evidence-led short-form opportunity intelligence for agencies and consumer teams.</p>
        <span>Independent product · Configured monitored samples · No guaranteed virality</span>
      </div>
      <nav className={styles.footerLinks} aria-label="Footer navigation">
        <div><h2>Product</h2><a href="#product">Overview</a><Link href="/dashboard">Dashboard</Link><a href="#pricing">Pricing</a></div>
        <div><h2>Company</h2><a href="#solutions">For agencies</a><Link href="/legal/contact">Contact</Link></div>
        <div><h2>Trust</h2><Link href="/legal/methodology">Methodology</Link><Link href="/legal/security">Security</Link><Link href="/legal/privacy">Privacy</Link></div>
        <div><h2>Legal</h2><Link href="/legal/terms">Terms</Link><Link href="/legal/cookies">Cookies</Link><Link href="/legal/ai-disclosure">AI disclosure</Link></div>
        <div><h2>Follow</h2><a href="https://t.me/signalsscope" target="_blank" rel="noopener noreferrer">Telegram <span aria-hidden="true">↗</span></a></div>
      </nav>
      <div className={styles.footerBase}><span>© 2026 SignalScope</span><span>Current preview: toys and family · Simulated data</span><span>Not affiliated with TikTok or ByteDance</span></div>
    </footer>
  </div>;
}
