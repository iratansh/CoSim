import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { authorizedClient } from '../api/client';
import { createOrganization, fetchOrganizations } from '../api/organizations';
import type { Project } from '../api/types';
import { useAuth } from '../hooks/useAuth';
import ChatBot from '../components/ChatBot';

import '../styles/landing.css';

const slugify = (value: string): string =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || 'workspace';

const LandingPage = () => {
  const navigate = useNavigate();
  const { token } = useAuth();

  const [launchState, setLaunchState] = useState<'idle' | 'launching' | 'success' | 'error'>('idle');
  const [launchMessage, setLaunchMessage] = useState<string>('');

  const handleLaunchConsole = useCallback(() => {
    if (token) {
      navigate('/projects');
    } else {
      navigate('/login');
    }
  }, [navigate, token]);

  const handleGetStarted = useCallback(() => {
    const targetId = token ? 'workflow' : 'benefits';
    document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth' });
  }, [token]);

  const handleStartWorkspace = useCallback(() => {
    if (token) {
      navigate('/projects');
    } else {
      document.getElementById('workflow')?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [navigate, token]);

  const openMail = useCallback((address: string, subject: string) => {
    window.open(`mailto:${address}?subject=${encodeURIComponent(subject)}`, '_blank');
  }, []);

  const openDocs = useCallback((url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  }, []);

  const launchFreeWorkspace = useCallback(async () => {
    if (!token) {
      navigate('/login');
      return;
    }

    setLaunchState('launching');
    setLaunchMessage('Preparing your starter workspace…');

    try {
      const organizations = await fetchOrganizations(token);
      const organization = organizations[0] ??
        (await createOrganization(token, {
          name: 'Personal Robotics Lab',
          slug: slugify(`personal-${Date.now().toString(36)}`)
        }));

      const client = authorizedClient(token);
      const projectName = 'Starter Robotics Workspace';
      const { data: project } = await client.post<Project>('/v1/projects', {
        name: projectName,
        slug: slugify(`${projectName}-${Date.now().toString(36).slice(2, 6)}`),
        organization_id: organization.id,
        description: 'Auto-generated workspace to explore the CoSim IDE'
      });

      const workspaceName = 'Main Simulation Lab';
      await client.post('/v1/workspaces', {
        project_id: project.id,
        name: workspaceName,
        slug: slugify(`${workspaceName}-${Date.now().toString(36).slice(2, 6)}`)
      });

      setLaunchState('success');
      setLaunchMessage('Workspace ready! Redirecting you now…');

      setTimeout(() => {
        navigate(`/projects/${project.id}`);
      }, 900);
    } catch (error) {
      console.error('Failed to launch workspace', error);
      setLaunchState('error');
      setLaunchMessage('Something went wrong while provisioning your workspace. Please try again.');
    }
  }, [navigate, token]);

  const launchStatus = useMemo(
    () => ({
      visible: launchState !== 'idle',
      state: launchState,
      message: launchMessage
    }),
    [launchMessage, launchState]
  );

  return (
    <div className="landing__root">
      <header className="landing__nav container">
        <div className="landing__logo">CoSim Cloud Robotics</div>
        <nav className="landing__navLinks">
          <button className="landing__ghost" onClick={() => navigate('/pricing')}>Pricing</button>
          <button className="landing__ghost" onClick={() => navigate('/login')}>Sign in</button>
          <button className="landing__cta" onClick={handleLaunchConsole}>Launch Console</button>
        </nav>
      </header>

      <main className="landing__hero container">
        <section className="landing__heroContent">
          <div className="landing__pill">Collaborative cloud IDE for robotics teams</div>
          <h1>Launch shared simulators and AI training pods in seconds.</h1>
          <p>
            Build SLAM pipelines, train MuJoCo & PyBullet agents, and co-edit C++ or Python in real time.
            CoSim provisions reproducible environments with live telemetry, cost guardrails, and GPU-aware scheduling.
          </p>
          <div className="landing__heroActions">
            <button className="landing__cta" onClick={handleGetStarted}>
              {token ? 'Open my workspaces' : 'Discover CoSim'}
            </button>
            <button className="landing__ghost" onClick={() => document.getElementById('benefits')?.scrollIntoView({ behavior: 'smooth' })}>Explore platform</button>
            <button className="landing__ghost" onClick={() => navigate('/pricing')}>View pricing</button>
          </div>
          <div className="landing__stats">
            <article>
              <strong>30s</strong>
              <span>CPU workspace boot time</span>
            </article>
            <article>
              <strong>5+</strong>
              <span>Live collaborators per session</span>
            </article>
            <article>
              <strong>90%</strong>
              <span>Quota guardrails enforced automatically</span>
            </article>
          </div>
        </section>
        <section className="landing__preview">
          <div className="landing__previewOrbs" />
          <div className="landing__previewCard">
            <div className="landing__previewHeader">
              <span className="landing__previewTitle">Session Timeline</span>
              <span className="landing__previewStatus">RUNNING</span>
            </div>
            <ul>
              <li>
                <span>09:42</span>
                <div>
                  <h4>Team synced MuJoCo workspace</h4>
                  <p>Auto-mounted datasets + GPU pool requested.</p>
                </div>
              </li>
              <li>
                <span>09:48</span>
                <div>
                  <h4>Shared IDE live coding</h4>
                  <p>Loop closures fixed collaboratively with inline comments.</p>
                </div>
              </li>
              <li>
                <span>09:57</span>
                <div>
                  <h4>Simulation snapshot</h4>
                  <p>State checkpoint pushed to org template for future runs.</p>
                </div>
              </li>
            </ul>
          </div>
        </section>
      </main>

      <section id="benefits" className="landing__benefits container">
        <h2>Why teams choose CoSim</h2>
        <p>Deploy robotics-ready infrastructure with the guardrails, observability, and workflows you need to move fast without surprises.</p>
        <div className="landing__benefitGrid">
          {BENEFITS.map(benefit => (
            <article key={benefit.title} className="landing__benefitCard">
              <div className="landing__benefitIcon">{benefit.icon}</div>
              <h3>{benefit.title}</h3>
              <p>{benefit.description}</p>
              <ul>
                {benefit.highlights.map(highlight => (
                  <li key={highlight}>{highlight}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section id="workflow" className="landing__workflow">
        <div className="container landing__workflowContent">
          <div className="landing__workflowCopy">
            <h2>One-click from prototype to large-scale training</h2>
            <p>
              Spin up CPU-only sessions for quick SLAM iteration, then escalate to GPU-backed RL jobs—all from the same collaborative workspace.
              Deterministic snapshots ensure every teammate has identical environments and simulator state.
            </p>
            <button className="landing__cta" onClick={handleStartWorkspace}>
              {token ? 'Go to workspace dashboard' : 'See how workspace flows work'}
            </button>
          </div>
          <div className="landing__workflowPanel">
            {WORKFLOW_STEPS.map(step => (
              <article key={step.step} className="landing__workflowStep">
                <span className="landing__workflowIndex">{step.step}</span>
                <div>
                  <h4>{step.title}</h4>
                  <p>{step.description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="landing__ctaSection container">
        <div className="landing__ctaCard">
          <h2>Ready to orchestrate your robotics stack?</h2>
          <p>Join early adopters combining robotics simulation, collaborative IDEs, and AI training on a single platform.</p>
          <div className="landing__ctaButtons">
            <button
              className="landing__cta"
              onClick={launchFreeWorkspace}
              disabled={launchState === 'launching'}
            >
              {launchState === 'launching' ? 'Launching…' : 'Launch free workspace'}
            </button>
            <button className="landing__ghost" onClick={() => openMail('sales@cosim.dev', 'Request a CoSim Guided Tour')}>
              Schedule a guided tour
            </button>
            <button className="landing__ghost" onClick={() => navigate('/pricing')}>
              Compare plans
            </button>
          </div>
          {launchStatus.visible && (
            <p className={`landing__launchStatus landing__launchStatus--${launchStatus.state}`}>
              {launchStatus.message}
            </p>
          )}
        </div>
      </section>

      <footer className="landing__footer">
        <div className="container landing__footerContent">
          <span>© {new Date().getFullYear()} CoSim Cloud Robotics</span>
          <nav>
            <button type="button" onClick={() => document.getElementById('benefits')?.scrollIntoView({ behavior: 'smooth' })}>Platform</button>
            <button type="button" onClick={() => navigate('/pricing')}>Pricing</button>
            <button type="button" onClick={() => openDocs('https://trust.cosim.dev')}>Security</button>
            <button type="button" onClick={() => openDocs('https://docs.cosim.dev')}>Docs</button>
            <button type="button" onClick={() => openMail('support@cosim.dev', 'CoSim Support Request')}>Support</button>
          </nav>
        </div>
      </footer>

      {/* AI Chatbot */}
      <ChatBot />
    </div>
  );
};

const BENEFITS = [
  {
    title: 'Collaboration without friction',
    description:
      'Pair program in a shared VS Code environment with presence, comments, and CRDT-powered edits.',
    icon: '🤝',
    highlights: ['Live cursors & audio rooms', 'Branch-free notebook sharing', 'Inline simulator annotations']
  },
  {
    title: 'Robotics simulators on demand',
    description:
      'MuJoCo and PyBullet workspaces are pre-baked with datasets, sensor mocks, and reproducible seeds.',
    icon: '🦾',
    highlights: ['GPU-aware scheduling', 'Snapshot & replay', 'Integrated telemetry overlays']
  },
  {
    title: 'Guardrails for cost & compliance',
    description:
      'Automatic quota caps, org-wide policies, and audit trails keep usage aligned with budget and policy.',
    icon: '🛡️',
    highlights: ['Quota dashboards', 'Multi-tenant isolation', 'SOC2-ready logging']
  }
] as const;

const WORKFLOW_STEPS = [
  {
    step: '01',
    title: 'Hydrate a workspace template',
    description: 'Pick SLAM, RL, or barebones C++/Python starter packs with dependencies pre-configured.'
  },
  {
    step: '02',
    title: 'Invite your robotics team',
    description: 'Onboard collaborators instantly—share links, assign roles, and co-edit files & configs.'
  },
  {
    step: '03',
    title: 'Launch shared simulators',
    description: 'Run MuJoCo/PyBullet side-by-side with the IDE; control scenarios via synced control plane.'
  },
  {
    step: '04',
    title: 'Scale experiments confidently',
    description: 'Spin up GPU-backed training jobs with cost guardrails and observability baked in.'
  }
] as const;

export default LandingPage;
