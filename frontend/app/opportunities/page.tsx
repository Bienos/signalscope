import {DataModeBanner} from '../../components/toys/DataModeBanner';
import {OpportunityWorkspace} from '../../components/toys/OpportunityWorkspace';
import {getToyOpportunities, getToySignals} from '../../lib/toys/api';

export const metadata = {title: 'Toy opportunities'};

export default async function Page({searchParams}: {searchParams: Promise<{signal?: string}>}) {
  const [signals, opportunities, params] = await Promise.all([getToySignals(), getToyOpportunities(), searchParams]);
  return <>
    <header className="pagehead"><div><div className="eyebrow">Decision and briefing workspace</div><h1 className="title">Opportunities</h1><p className="subtitle">Turn evidence into a persistent Act, Monitor or Avoid decision, then create an original toy-content brief linked to its source signal.</p></div></header>
    <DataModeBanner mode={signals.mode} modeLabel={signals.mode_label} coverage={signals.coverage} provider={signals.provider} lastObservation={signals.last_observation}/>
    <OpportunityWorkspace signals={signals.items} initialOpportunities={opportunities.items} initialSignalId={params.signal}/>
  </>;
}
