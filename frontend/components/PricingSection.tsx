import Link from 'next/link';
import {plans} from '../lib/commercial';
import styles from './PricingSection.module.css';

export function PricingSection() {
  return <section className="landingPricing" id="pricing">
    <div className="landingPricingIntro">
      <span>INDICATIVE LAUNCH PRICING</span>
      <h2>Start with one category. Scale across clients and teams.</h2>
      <p>The commercial model is designed around category watchlists, research depth and team workflow. The current free product preview uses simulated toy data; additional categories remain planned.</p>
    </div>
    <div className={`landingPlanGrid ${styles.planGrid}`}>{plans.map((plan) => <article id={plan.id === 'enterprise' ? 'enterprise' : undefined} key={plan.id} className={plan.recommended ? 'featured' : ''}><span>{plan.name}</span><b>{plan.monthly ? `€${plan.monthly}/mo` : plan.id === 'free' ? '€0' : 'Custom'}</b><p>{plan.audience}</p><small className={styles.limit}>{plan.limits.monitors}</small></article>)}</div>
    <Link className="action" href="/pricing">Compare plans and add-ons <span aria-hidden="true">→</span></Link>
  </section>;
}
