import { useMemo, useState } from 'react';
import { NavigateFunction, useNavigate } from 'react-router-dom';

import '../styles/pricing.css';

type BillingCycle = 'monthly' | 'annual';

type PlanId = 'free' | 'student' | 'pro' | 'team' | 'enterprise';

interface Plan {
  id: PlanId;
  name: string;
  tagline: string;
  monthlyPrice: number | null;
  annualPrice: number | null;
  highlight?: boolean;
  badge?: string;
  features: string[];
  includes: string[];
  ctaLabel?: string;
}

const PLANS: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    tagline: 'Solo builders exploring collaborative robotics',
    monthlyPrice: 0,
    annualPrice: 0,
    features: [
      '2 vCPU / 4 GB RAM workspaces',
      'MuJoCo & PyBullet runtime presets',
      'Shared IDE with CRDT autosave',
      '1 active simulator stream'
    ],
    includes: ['Community support', 'Monthly usage summaries', 'Single workspace template']
  },
  {
    id: 'student',
    name: 'Student',
    tagline: 'Hands-on labs for academic teams and research clubs',
    monthlyPrice: 12,
    annualPrice: 120,
    features: [
      '4 vCPU / 8 GB RAM workspaces',
      'GPU bursts for RL up to 20 hrs/mo',
      'Team presence indicators & chat',
      'Course roster provisioning'
    ],
    includes: ['Email support within 1 business day', 'Classroom templates', 'Roster import via CSV'],
    badge: 'Best for learning'
  },
  {
    id: 'pro',
    name: 'Pro',
    tagline: 'Scaling pods for robotics startups and research labs',
    monthlyPrice: 39,
    annualPrice: 390,
    highlight: true,
    features: [
      'Custom workspace presets & secrets',
      'Always-on GPU pools with quota guardrails',
      'Automated snapshot + restore',
      'Observability dashboards & alerts'
    ],
    includes: ['Priority support (4h SLA)', 'Role-based access controls', 'SAML SSO add-on'],
    badge: 'Most popular',
    ctaLabel: 'Start Pro trial'
  },
  {
    id: 'team',
    name: 'Team',
    tagline: 'Multi-project orchestration for robotics departments',
    monthlyPrice: 99,
    annualPrice: 990,
    features: [
      'Org-wide usage policies & approvals',
      'Dedicated GPU pools with preemption handling',
      'Advanced simulator recording & replay',
      'Enterprise-grade secrets management'
    ],
    includes: ['24/7 on-call support', 'Custom onboarding workshop', 'Audit-ready reporting'],
    badge: 'Scale ready',
    ctaLabel: 'Talk to sales'
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    tagline: 'Global robotics programs with compliance requirements',
    monthlyPrice: null,
    annualPrice: null,
    features: [
      'Regional data residency & air-gapped clusters',
      'Private simulator pipelines with hardware-in-loop',
      'Granular policy engine & cost center billing',
      'Dedicated success manager & solution architects'
    ],
    includes: ['Custom security reviews', 'White-glove migration support', '99.9% uptime SLA'],
    badge: 'Custom'
  }
];

const FAQ_ITEMS = [
  {
    question: 'Can we mix plans inside one organization?',
    answer:
      'Yes. Upgrade individual workspaces or teams as needed. Billing rolls up to the organization owner with per-plan usage breakdowns.'
  },
  {
    question: 'Do you offer educational discounts?',
    answer:
      'Academic institutions automatically qualify for Student pricing. Contact us for campus-wide licensing or volume discounts.'
  },
  {
    question: 'How does GPU usage work?',
    answer:
      'Student plans include a pooled allowance. Pro and above can reserve dedicated GPU pools with guardrails—unused minutes roll over month to month.'
  },
  {
    question: 'Can we self-host CoSim?',
    answer:
      'Enterprise customers can deploy in private clouds or on-prem clusters. The control plane, simulators, and collaboration services ship as hardened Helm charts.'
  }
];

const PricingPage = () => {
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState<BillingCycle>('monthly');

  const subtitle = useMemo(() => {
    return billingCycle === 'monthly'
      ? 'Flexible monthly subscriptions. Upgrade or pause anytime.'
      : 'Annual plans include two months free and quarterly strategy reviews.';
  }, [billingCycle]);

  return (
    <div className="pricing__root">
      <header className="pricing__nav container">
        <div className="pricing__logo" onClick={() => navigate('/')}>CoSim Cloud Robotics</div>
        <nav className="pricing__actions">
          <button className="pricing__ghost" onClick={() => navigate('/')}>Home</button>
          <button className="pricing__ghost" onClick={() => navigate('/login')}>Sign in</button>
          <button className="pricing__cta" onClick={() => navigate('/login')}>Launch Console</button>
        </nav>
      </header>

      <main className="pricing__hero container">
        <section className="pricing__intro">
          <div className="pricing__pill">Choose the runway that fits your robotics roadmap</div>
          <h1>Bring your entire robotics stack to the cloud—without surprise costs.</h1>
          <p>{subtitle}</p>

          <div className="pricing__toggle">
            <button
              className={billingCycle === 'monthly' ? 'pricing__toggleBtn active' : 'pricing__toggleBtn'}
              onClick={() => setBillingCycle('monthly')}
            >
              Monthly
            </button>
            <button
              className={billingCycle === 'annual' ? 'pricing__toggleBtn active' : 'pricing__toggleBtn'}
              onClick={() => setBillingCycle('annual')}
            >
              Annual <span className="pricing__toggleBadge">2 months free</span>
            </button>
          </div>
        </section>

        <section className="pricing__grid">
          {PLANS.map(plan => (
            <article
              key={plan.id}
              className={`pricing__card${plan.highlight ? ' highlight' : ''}`}
            >
              {plan.badge && <span className="pricing__badge">{plan.badge}</span>}
              <header>
                <h2>{plan.name}</h2>
                <p>{plan.tagline}</p>
                {renderPrice(plan, billingCycle)}
              </header>

              <div className="pricing__section">
                <h3>What you get</h3>
                <ul>
                  {plan.features.map(feature => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
              </div>

              <div className="pricing__section">
                <h3>Also includes</h3>
                <ul>
                  {plan.includes.map(line => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>

              <button
                className={`pricing__planCta${plan.highlight ? ' primary' : ''}`}
                onClick={() => handlePlanCta(plan, navigate)}
              >
                {plan.ctaLabel ?? (plan.monthlyPrice === 0 ? 'Start for free' : 'Request access')}
              </button>
            </article>
          ))}
        </section>
      </main>

      <section className="pricing__extras">
        <div className="container pricing__extrasContent">
          <div className="pricing__extrasCard">
            <h2>Need a custom bundle?</h2>
            <p>
              Combine self-hosted simulators, hardware-in-the-loop labs, or on-premise GPU fleets. Our solutions team will tailor
              CoSim to your mission profile and compliance stack.
            </p>
            <div className="pricing__extrasActions">
              <button className="pricing__cta" onClick={() => navigate('/login')}>Book a consultation</button>
              <button className="pricing__ghost" onClick={() => navigate('/login')}>Download spec sheet</button>
            </div>
          </div>
        </div>
      </section>

      <section className="pricing__faq container">
        <h2>Frequently asked questions</h2>
        <div className="pricing__faqGrid">
          {FAQ_ITEMS.map(item => (
            <article key={item.question} className="pricing__faqCard">
              <h3>{item.question}</h3>
              <p>{item.answer}</p>
            </article>
          ))}
        </div>
      </section>

      <footer className="pricing__footer">
        <div className="container pricing__footerContent">
          <span>© {new Date().getFullYear()} CoSim Cloud Robotics</span>
          <nav>
            <button onClick={() => navigate('/')}>Home</button>
            <button onClick={() => navigate('/login')}>Docs</button>
            <button onClick={() => navigate('/login')}>Support</button>
            <button onClick={() => navigate('/login')}>Status</button>
          </nav>
        </div>
      </footer>
    </div>
  );
};

const renderPrice = (plan: Plan, cycle: BillingCycle) => {
  const price = cycle === 'annual' ? plan.annualPrice : plan.monthlyPrice;
  if (price === null) {
    return <div className="pricing__price">Custom pricing</div>;
  }

  if (price === 0) {
    return (
      <div className="pricing__price">
        <span className="pricing__priceValue">$0</span>
        <span className="pricing__priceMeta">per builder {cycle === 'annual' ? 'annually' : 'monthly'}</span>
      </div>
    );
  }

  const formatted = cycle === 'annual'
    ? `$${price.toLocaleString()}`
    : `$${price.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

  return (
    <div className="pricing__price">
      <span className="pricing__priceValue">{formatted}</span>
      <span className="pricing__priceMeta">
        {cycle === 'annual' ? 'per builder / year' : 'per builder / month'}
      </span>
    </div>
  );
};

const handlePlanCta = (plan: Plan, navigate: NavigateFunction) => {
  if (plan.id === 'team' || plan.id === 'enterprise') {
    navigate('/login');
    return;
  }

  navigate('/login');
};

export default PricingPage;
