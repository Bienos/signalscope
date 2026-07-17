import Link from 'next/link';
import {ReportExports} from '../../components/ReportActions';
import {DataModeBanner} from '../../components/toys/DataModeBanner';
import {SignalCard} from '../../components/toys/SignalCard';
import {GenerateToyReport} from '../../components/toys/ToyReportActions';
import {getToyReports} from '../../lib/toys/api';

export const metadata = {title: 'Toy decision reports'};

export default async function Page() {
  const reports = await getToyReports();
  return <>
    <header className="reporthead"><div><div className="eyebrow">Client-ready decision brief</div><h1 className="title">Reports</h1><p className="subtitle">Lead with what the team should do, then show the evidence, safety checks and limitations supporting the recommendation.</p></div><GenerateToyReport/></header>
    <DataModeBanner mode={reports.mode} modeLabel={reports.mode_label} coverage={reports.coverage} provider={reports.provider} lastObservation={reports.last_observation}/>
    {!reports.items.length && <div className="empty"><b>No report exists yet.</b><p>Select opportunities and complete review before generating a report.</p></div>}
    {reports.items.map((report) => <article className="decisionreport" key={report.id}>
      <header><div><span className="lifecyclepill">{report.status}</span><h2>Toy trend decision brief · {report.date}</h2></div>{typeof report.id === 'number' && <ReportExports id={report.id}/>}</header>
      <section className="reportexecutive"><span className="eyebrow">1 · Executive summary</span><h3>What changed and what to do next</h3><p>{report.executive_summary}</p></section>
      <ReportSignalSection index="2" title="Act now" signals={report.act}/>
      <ReportSignalSection index="3" title="Monitor" signals={report.monitor}/>
      <ReportSignalSection index="4" title="Avoid or hold" signals={report.avoid}/>
      <section><span className="eyebrow">5 · Emerging toy categories</span><h3>Category movement</h3><TagList values={unique([...report.act, ...report.monitor].map((signal) => signal.category))}/></section>
      <section><span className="eyebrow">6 · Emerging creators and hashtags</span><h3>Supporting entities</h3><p>Open Track to inspect creator, hashtag and sound evidence within the configured sample.</p><Link href="/track">Open Track →</Link></section>
      <section><span className="eyebrow">7 · Content mechanisms</span><h3>Repeatable mechanisms</h3><TagList values={unique([...report.act, ...report.monitor].map((signal) => signal.mechanism))}/></section>
      <section><span className="eyebrow">8 · Creative opportunities</span><h3>Source-linked briefs</h3><div className="briefcards">{report.opportunities.map((item) => <article className="panel" key={item.id}><h4>{item.title}</h4><p>{item.original_hook}</p><Link href={`/signals/${item.signal_id}`}>Source evidence →</Link></article>)}</div></section>
      <section className="reportlimitations"><span className="eyebrow">9 · Safety, originality and evidence</span><h3>Limitations that must travel with the report</h3><ul>{report.limitations.map((item) => <li key={item}>{item}</li>)}</ul></section>
      <section><span className="eyebrow">10 · Methodology</span><h3>How this report was prepared</h3><p>{report.methodology}</p><Link href="/workspace?tab=methodology">Read methodology →</Link></section>
      <footer><b>Analyst exports</b><p>CSV, XLSX and HTML are secondary working formats. They do not replace the decision summary and evidence limitations above.</p></footer>
    </article>)}
  </>;
}

function ReportSignalSection({index, title, signals}: {index: string; title: string; signals: import('../../lib/toys/types').ToySignal[]}) {
  return <section><span className="eyebrow">{index} · {title}</span><h3>{title}</h3>{signals.length ? <div className="reportcards">{signals.map((signal) => <SignalCard signal={signal} compact key={signal.id}/>)}</div> : <p>No selected signals.</p>}</section>;
}
function TagList({values}: {values: string[]}) { return <div className="taglist">{values.map((value) => <span key={value}>{value}</span>)}</div>; }
function unique(values: string[]) { return Array.from(new Set(values)); }
