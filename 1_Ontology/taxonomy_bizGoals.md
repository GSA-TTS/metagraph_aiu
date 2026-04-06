# Taxonomy of Business Goals

Each goal cluster includes a **lookup-fields** bullet that maps to fields from the 2024 Federal AI Use Case Inventory `data_dictionary.yaml` (conceptually: “which fields most likely contain this kind of goal signal?”).

Where field names vary slightly by agency, assume canonical names from OMB’s AI use case inventory guidance such as:
- `use_case_name`
- `intended_purpose_and_expected_benefits`
- `problem_to_be_solved` (if present)
- `ai_system_outputs`
- `mission_or_topic_area`
- `business_function_or_program_area`
- `rights_impacting`, `safety_impacting`, `pii_impacted`, `demographics_used`
- `stage_of_development` / `lifecycle_stage`
- `agency`, `component_or_bureau`


## 1. Strategic and Business Model Goals

### 1.1 Direction, ambition, and coherence

- Define a clear, credible mission, vision, and purpose that accurately reflect reality and guide decisions.  
- Align purpose, strategy, and goals so ambitions are grounded in capabilities and market evidence.  
- Harmonize objectives across functions to eliminate conflicting priorities and resource dilution.  
- Translate strategy into actionable, measurable objectives cascaded through the organization.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – language about “mission”, “purpose”, “strategic objectives”, “supporting agency mission”.  
- `problem_to_be_solved` – statements about misalignment or lack of clarity in direction (where present).  
- `mission_or_topic_area` – anchor strategic goals in the relevant mission domain.  
- `business_function_or_program_area` – shows where strategy must translate into objectives.  
- `use_case_name` – short labels like “Strategic Planning Analytics”, “Mission Alignment Dashboard”.

### 1.2 Strategic fit, market choices, and portfolio moves

- Enter and expand in markets where the firm has strong strategic and capability fit.  
- Pursue M&A only when there is a clear, evidence‑based strategic rationale and realizable synergies.  
- Focus diversification on opportunities that leverage shared customers, capabilities, or platforms.  
- Continuously anticipate competitive dynamics and substitutes and adjust strategy accordingly.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – text about “market analysis”, “strategy evaluation”, “portfolio optimization”, “expansion planning”.  
- `problem_to_be_solved` – mentions of “market entry”, “portfolio fit”, “synergy assessment”.  
- `mission_or_topic_area` – to tag which external markets or policy domains strategy relates to.  
- `ai_system_outputs` – outputs like “market segmentation”, “scenario analysis”, “portfolio simulations”.  
- `business_function_or_program_area` – “strategy”, “corporate planning”, “policy analysis”.

### 1.3 Business model design and economics

- Design business models with compelling value propositions, viable revenue streams, and sustainable cost structures.  
- Align pricing, channels, and partnerships with target customer needs and willingness to pay.  
- Regularly test and refine business models to maintain economic viability as conditions change.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – phrases like “optimize pricing”, “evaluate business model viability”, “assess revenue/cost structure”.  
- `problem_to_be_solved` – “unsustainable economics”, “unprofitable segments”, “pricing uncertainty”.  
- `ai_system_outputs` – “profitability analytics”, “elasticity estimates”, “scenario projections”.  
- `business_function_or_program_area` – “finance”, “strategy”, “product management”.

### 1.4 Strategic planning and scaling under uncertainty

- Build strategic plans that incorporate uncertainty, scenarios, and real options, not just point forecasts.  
- Scale initiatives at a pace that matches organizational capabilities and risk appetite.  
- Continuously learn from outcomes to refine strategic assumptions and choices.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “scenario planning”, “forecasting under uncertainty”, “capacity planning”, “resource allocation”.  
- `ai_system_outputs` – “scenario sets”, “risk-adjusted forecasts”, “capacity utilization projections”.  
- `stage_of_development` – to distinguish planning/experiment vs. scaled deployment.  
- `mission_or_topic_area` – “enterprise management/strategy”, “internal operations”.


## 2. Market, Customer, and Revenue Goals

### 2.1 Brand positioning, identity, and value communication

- Articulate a distinctive, specific brand positioning for clearly defined target audiences.  
- Maintain coherent brand identity and experiences across all touchpoints.  
- Communicate value with concrete proof points that build trust and differentiation.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “improve messaging”, “brand monitoring”, “public sentiment analysis”, “campaign optimization”.  
- `ai_system_outputs` – “sentiment scores”, “topic clusters”, “messaging insights”.  
- `mission_or_topic_area` – “communications”, “public affairs”, “outreach”.  
- `business_function_or_program_area` – “marketing”, “public engagement”.

### 2.2 Market understanding, demand estimation, and segmentation

- Define markets and opportunity sizes realistically based on customer behavior.  
- Develop evidence‑based customer segmentation that reflects real differences in needs and value.  
- Understand customer jobs‑to‑be‑done and alternatives to inform offerings and messaging.  
- Use scenario‑based demand forecasting and sensitivity analysis for investment decisions.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “segment customers”, “forecast demand”, “analyze usage patterns”, “identify target groups”.  
- `ai_system_outputs` – “segment labels”, “demand forecasts”, “propensity scores”.  
- `mission_or_topic_area` – program/benefit area being forecast.  
- `business_function_or_program_area` – “policy analysis”, “program design”, “market research”.

### 2.3 Customer acquisition, conversion, and go‑to‑market

- Clarify ideal customer profiles and target acquisition efforts accordingly.  
- Design channel strategies that match buyer journeys and economics.  
- Tailor messaging and journeys by stage to improve conversion.  
- Optimize customer acquisition cost, payback, and funnel handoffs between teams.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “improve outreach effectiveness”, “target the right beneficiaries/participants”, “optimize campaigns”.  
- `ai_system_outputs` – “propensity to respond”, “channel attribution”, “campaign performance dashboards”.  
- `mission_or_topic_area` – domains where outreach or enrollment is key (e.g., health, benefits).  
- `business_function_or_program_area` – “outreach”, “communications”, “program enrollment”.

### 2.4 Customer experience, satisfaction, and retention

- Deliver low‑friction, reliable customer journeys across key touchpoints.  
- Build responsive, well‑equipped service and support capabilities.  
- Use customer data to personalize interactions and improve perceived value.  
- Systematically collect feedback and act on early churn signals.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “improve customer experience”, “reduce complaints”, “enhance satisfaction”, “increase retention”.  
- `ai_system_outputs` – “CX scores”, “churn risk scores”, “feedback themes”, “journey analytics”.  
- `business_function_or_program_area` – “customer service”, “benefits administration”, “contact center”.  
- `mission_or_topic_area` – specific service areas (e.g., “public-facing services”).


## 3. Product, Service, and Innovation Goals

### 3.1 Product–market fit and offer configuration

- Validate demand and problem–solution fit with behavioral evidence before scaling.  
- Align pricing and revenue models with customer value perception and usage.  
- Right‑size feature sets so offerings fully solve priority jobs without overengineering.  
- Scale go‑to‑market only after achieving robust product–market fit.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “evaluate program effectiveness”, “assess uptake”, “test new offering or policy design”.  
- `problem_to_be_solved` – “low uptake”, “poor fit”, “misaligned offering”.  
- `ai_system_outputs` – “uptake prediction”, “usage clustering”, “A/B test analytics”.  
- `mission_or_topic_area` / `business_function_or_program_area` – where the program/product sits.

### 3.2 Quality, reliability, and consistency

- Ensure products and services reliably perform as intended under real conditions.  
- Consistently deliver on commitments (e.g., timeliness, specifications).  
- Provide consistent experiences across channels, locations, and time.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “improve service reliability”, “reduce errors”, “monitor quality of service”, “ensure timeliness”.  
- `ai_system_outputs` – “quality metrics”, “SLAs adherence dashboards”, “anomaly alerts”.  
- `business_function_or_program_area` – areas with performance targets (e.g., transportation, utilities, benefits processing).  

### 3.3 Innovation pace and responsiveness

- Maintain innovation cycles that keep pace with technology, competitors, and customer needs.  
- Invest in R&D and experimentation aligned with strategic priorities.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “support R&D”, “identify innovation opportunities”, “monitor emerging technologies”.  
- `ai_system_outputs` – “trend analyses”, “technology scanning results”.  
- `stage_of_development` – early-stage pilots often associated with innovation goals.

### 3.4 Product portfolio and lifecycle management

- Actively manage the product portfolio, including timely retirement of legacy offerings.  
- Allocate resources across offerings based on strategic fit and performance.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “rationalize portfolio”, “prioritize programs”, “support decommission decisions”.  
- `ai_system_outputs` – “portfolio performance dashboards”, “priority rankings”.  
- `mission_or_topic_area` / `business_function_or_program_area` – which portfolio (programs, services, assets).  


## 4. Operational and Process Goals

### 4.1 Process efficiency and waste reduction

- Design and run processes that minimize waste (defects, waiting, overprocessing, unnecessary movement, etc.).  
- Identify and relieve bottlenecks to stabilize flow and throughput.  
- Standardize work where appropriate to reduce variability and errors.  
- Improve process visibility and measurement to support daily management.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “reduce processing time”, “increase throughput”, “streamline workflow”, “reduce rework”.  
- `problem_to_be_solved` – “backlogs”, “bottlenecks”, “manual effort”.  
- `ai_system_outputs` – “process metrics”, “queue forecasts”, “bottleneck identification”, “workload predictions”.  
- `business_function_or_program_area` – “case processing”, “claims”, “licensing”, “back-office operations”.

### 4.2 Supply chain, logistics, inventory, and fulfillment

- Strengthen upstream and internal operations to reduce supply chain disruptions.  
- Improve logistics reliability and resilience to external shocks.  
- Optimize inventory levels to balance availability, cost, and risk of obsolescence.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “optimize inventory”, “improve logistics planning”, “reduce stockouts”, “enhance fulfillment”.  
- `ai_system_outputs` – “demand forecasts”, “routing plans”, “inventory recommendations”, “risk scores on suppliers”.  
- `mission_or_topic_area` – where physical goods or critical supplies are managed (e.g., emergency management, logistics).  

### 4.3 Internal controls, procedures, and performance management

- Establish robust internal controls and clear procedures that support compliant, reliable operations.  
- Use performance metrics and feedback loops to continuously improve processes.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “monitor internal control effectiveness”, “support compliance checks”, “improve accuracy of reporting”.  
- `ai_system_outputs` – “control exceptions”, “risk alerts”, “performance dashboards”.  
- `rights_impacting`, `safety_impacting`, `pii_impacted` – to infer stronger control and oversight goals.  

### 4.4 Scaling operations without degrading quality or CX

- Scale volumes and complexity while maintaining quality and customer experience.  
- Invest in systems and capabilities ahead of demand to support growth.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “support scaling of operations”, “handle higher volumes without delay”, “maintain quality at scale”.  
- `ai_system_outputs` – “capacity forecasts”, “service level projections”, “load balancing recommendations”.  
- `stage_of_development` – deployed use cases with large volumes highlight scaling goals.  


## 5. Financial Structure and Performance Goals

### 5.1 Revenue stability, cash flow, and liquidity

- Reduce undue revenue volatility and earnings instability.  
- Align profit recognition with cash generation to avoid liquidity stress.  
- Improve cash‑flow forecasting and maintain adequate buffers and committed credit.  
- Reduce dependence on fragile short‑term funding.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “forecast revenue”, “monitor cash flow”, “assess financial risk”, “support budgeting”.  
- `ai_system_outputs` – “cash-flow forecasts”, “revenue projections”, “volatility indicators”.  
- `business_function_or_program_area` – “finance”, “budget office”, “treasury”.

### 5.2 Cost structure and inflation resilience

- Optimize fixed vs. variable costs to balance efficiency and resilience.  
- Increase cost flexibility to better absorb inflation and input‑cost shocks.  
- Enhance cost visibility and control at product, customer, and unit levels.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “analyze cost drivers”, “identify savings opportunities”, “support cost management”.  
- `ai_system_outputs` – “cost breakdowns”, “trend analytics”, “unit-cost benchmarks”.  

### 5.3 Profitability, ROI, and capital allocation

- Strengthen structural margins via better pricing power and efficiency.  
- Allocate capital to projects and business lines with superior risk‑adjusted returns.  
- Evaluate investments with disciplined, risk‑aware methods and consistent hurdle rates.  
- Conduct post‑investment reviews to learn and redeploy capital effectively.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “evaluate ROI”, “prioritize investments”, “optimize capital allocation”.  
- `ai_system_outputs` – “ROI estimates”, “project rankings”, “scenario NPVs”.  
- `business_function_or_program_area` – “investment planning”, “capital projects”.

### 5.4 Leverage, market risk, and financial risk management

- Maintain leverage at levels consistent with resilience and strategic flexibility.  
- Manage interest‑rate and refinancing risk proactively.  
- Systematically hedge or manage currency and other market risks where material.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “assess credit risk”, “monitor exposure to interest rates or FX”, “stress-test financial plans”.  
- `ai_system_outputs` – “risk scores”, “stress test results”, “exposure reports”.  
- `business_function_or_program_area` – “risk management”, “treasury”, “financial stability”.


## 6. Human Capital, Culture, and Organizational Goals

### 6.1 Talent, skills, and workforce strategy

- Align workforce skills and roles with strategic needs through forward‑looking planning.  
- Invest in upskilling, reskilling, and internal mobility to close skills gaps.  
- Offer competitive, compelling employment value propositions in critical roles.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “forecast workforce needs”, “identify skills gaps”, “optimize staffing”, “support recruitment”.  
- `ai_system_outputs` – “skill gap analyses”, “workforce forecasts”, “candidate ranking”.  
- `business_function_or_program_area` – “HR”, “workforce planning”, “training and development”.

### 6.2 Engagement, culture, and incentives

- Increase employee engagement by improving recognition, management quality, and growth opportunities.  
- Build healthy, inclusive cultures with psychological safety and clear communication.  
- Align incentives with long‑term value, quality, collaboration, and ethics.  
- Reduce organizational silos and align culture with strategic priorities.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “analyze employee feedback”, “monitor engagement”, “identify cultural issues”, “support DEIA goals”.  
- `ai_system_outputs` – “engagement scores”, “theme clusters from surveys”, “sentiment analysis of comments”.  
- `mission_or_topic_area` – “internal operations”, “workforce management”.  

### 6.3 Retention, burnout, and leadership pipelines

- Reduce avoidable turnover by addressing leadership, workload, and development drivers.  
- Design work and leadership practices that prevent burnout and support well‑being.  
- Build robust leadership pipelines and succession plans.  
- Improve people‑management quality at all levels.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “predict turnover risk”, “identify burnout risk”, “support succession planning”.  
- `ai_system_outputs` – “attrition predictions”, “risk scores by team or role”, “leadership pipeline analytics”.  

### 6.4 Organizational design and decision rights

- Align organizational structure with strategy to support coordination and agility.  
- Clarify roles, responsibilities, and handoffs to reduce friction and gaps.  
- Design clear decision rights and governance that enable timely, accountable decisions.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “map collaboration patterns”, “analyze org structure”, “optimize decision flows”.  
- `ai_system_outputs` – “network analyses”, “org diagnostics”, “bottleneck maps”.  
- `business_function_or_program_area` – “organization development”, “change management”.


## 7. Governance, Legal, and Compliance Goals

### 7.1 Regulatory and legal compliance

- Achieve and maintain compliance with applicable financial, data‑protection, safety, labor, tax, and environmental regulations.  
- Minimize exposure to fines, sanctions, and criminal liability through effective programs.  
- Implement robust, well‑resourced compliance functions and controls.  
- Strengthen monitoring, reporting, and documentation to evidence compliance.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “support regulatory compliance”, “automate compliance checks”, “monitor adherence to policy/law”.  
- `ai_system_outputs` – “compliance alerts”, “rule‑violation flags”, “monitoring logs”.  
- `rights_impacting`, `safety_impacting`, `pii_impacted` – indicate where compliance and legal goals are especially critical.  
- `business_function_or_program_area` – “compliance”, “legal”, “oversight”.

### 7.2 Governance structures and board effectiveness

- Ensure boards effectively oversee risk, safety, culture, and ethics, not just financials.  
- Increase board independence, challenge, and accountability.  
- Improve risk governance and information flow to the board from control functions.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “provide dashboards to leadership/board”, “support enterprise risk management”, “improve oversight”.  
- `ai_system_outputs` – “enterprise risk dashboards”, “aggregated indicators”, “board reporting packs”.  
- `mission_or_topic_area` – “enterprise management”, “governance”.

### 7.3 Contract management and intellectual‑property stewardship

- Improve contract lifecycle management to maximize value and minimize leakages.  
- Proactively manage auto‑renewals and deadlines to optimize commercial terms.  
- Protect and enforce intellectual property rights and manage IP disputes strategically.  
- Draft clear licensing and commercial terms that reduce ambiguity and dispute risk.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “analyze contracts”, “track renewals”, “identify obligations and risks”, “support IP management”.  
- `ai_system_outputs` – “contract summaries”, “clause classification”, “renewal alerts”, “IP risk flags”.  
- `business_function_or_program_area` – “procurement”, “legal”, “contracts office”.

### 7.4 Ethics, fraud, and whistleblowing

- Build and enforce effective ethics programs beyond “paper” codes.  
- Strengthen anti‑fraud controls and oversight in high‑risk areas.  
- Provide secure, trusted whistleblower channels and robust case management.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “detect fraud”, “monitor ethics violations”, “triage whistleblower reports”.  
- `ai_system_outputs` – “fraud risk scores”, “anomaly detection outputs”, “case prioritization”.  
- `rights_impacting` – where ethical and rights implications are most acute.  


## 8. Technology, Data, and Cybersecurity Goals

### 8.1 Technology and data alignment

- Align technology and data strategy with business priorities.  
- Modernize legacy systems to improve performance, flexibility, and integration.  
- Ensure data quality, governance, and accessibility for decision‑making.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “improve data quality”, “support data integration”, “modernize legacy systems”, “enable analytics”.  
- `ai_system_outputs` – “data quality scores”, “metadata catalogs”, “integration mappings”.  
- `business_function_or_program_area` – “IT”, “data office”, “CIO function”.

### 8.2 Cybersecurity and protection

- Strengthen cybersecurity to protect assets, data, and operations.  
- Detect and respond quickly to threats and vulnerabilities.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “detect cyber threats”, “monitor network activity”, “identify vulnerabilities”.  
- `ai_system_outputs` – “threat alerts”, “risk scores”, “anomaly flags”.  
- `pii_impacted`, `rights_impacting`, `safety_impacting` – elevate these cases as security‑critical.  

### 8.3 Automation and AI enablement

- Leverage automation and AI in ways that enhance productivity and manage risk.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “automate manual tasks”, “augment analysts”, “support decision-making”.  
- `ai_system_outputs` – any operational decision support or automation output fields.  
- `stage_of_development` – to track pilots vs. scaled automation.  


## 9. External Environment and Macroeconomic Goals

### 9.1 Macroeconomic resilience

- Build financial and operational resilience to downturns and demand shocks.  
- Strengthen pricing, cost, and sourcing strategies to handle inflation and input‑cost spikes.  
- Manage interest‑rate and capital‑access risks to sustain investment capacity.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “monitor macroeconomic indicators”, “assess exposure to downturns”, “support inflation or rate-sensitivity analysis”.  
- `ai_system_outputs` – “macroeconomic forecasts”, “stress-test simulations”, “exposure reports”.  
- `mission_or_topic_area` – “economic & financial”, “macroeconomic policy”.

### 9.2 Regulatory and policy adaptability

- Anticipate and adapt to tax, trade, and regulatory changes with minimal disruption.  
- Reduce compliance burden through efficient processes while staying within the law.  
- Protect access to contracts and markets amid policy shifts.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “analyze regulatory changes”, “assess policy impacts”, “support rulemaking analysis”.  
- `ai_system_outputs` – “policy impact models”, “scenario outcomes”, “change alerts”.  
- `mission_or_topic_area` – “regulation & policy”, “trade”, “tax”.

### 9.3 Resilience to geopolitical, pandemic, and disaster shocks

- Increase resilience of supply chains, operations, and markets to geopolitical conflict and trade disruptions.  
- Prepare for and respond effectively to pandemics and global health crises.  
- Enhance resilience to natural disasters and climate‑related events.  
- Secure access to critical energy and resources at sustainable cost.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “assess supply chain risk”, “support disaster response planning”, “monitor geopolitical risk”.  
- `ai_system_outputs` – “risk maps”, “event likelihood scores”, “resource allocation recommendations”.  
- `mission_or_topic_area` – “emergency management”, “public health”, “national security”.

### 9.4 Labor, demographic, and social shifts

- Adapt workforce strategies to demographic changes and mobility patterns.  
- Align skills development with automation and AI trends.  
- Reduce barriers to workforce participation (e.g., childcare, transport).  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “analyze labor market trends”, “assess demographics”, “support workforce participation initiatives”.  
- `ai_system_outputs` – “labor market forecasts”, “demographic analyses”.  
- `mission_or_topic_area` – “labor & workforce”, “education & training”.


## 10. Reputation, Brand, and Stakeholder Trust Goals

### 10.1 Product safety, data protection, and incident prevention

- Deliver safe, reliable products and services that protect customers from harm.  
- Protect personal and sensitive data through strong privacy and security practices.  
- Prevent safety and environmental incidents across operations and supply chains.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “monitor safety incidents”, “detect product issues”, “improve data protection”.  
- `ai_system_outputs` – “incident detection alerts”, “safety risk scores”, “privacy/compliance flags”.  
- `rights_impacting`, `safety_impacting`, `pii_impacted` – automatically highlight use cases where these trust goals are central.

### 10.2 Ethical conduct, compliance, and leadership integrity

- Uphold high ethical standards in business models, reporting, and leadership behavior.  
- Avoid fraud, manipulation, and misconduct that could erode stakeholder trust.  
- Ensure leaders embody and reinforce stated values.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “detect misconduct”, “monitor ethics compliance”, “identify conflicts of interest”.  
- `ai_system_outputs` – “ethics alerts”, “pattern analyses of anomalies”, “case risk scores”.  
- `rights_impacting` – indicates high-stakes ethical implications.

### 10.3 Crisis readiness and communications

- Respond quickly, transparently, and empathetically to crises and incidents.  
- Coordinate communications to avoid confusion, opacity, or tone‑deaf messaging.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “monitor media/social media”, “support crisis communications”, “detect emerging issues”.  
- `ai_system_outputs` – “real-time sentiment monitoring”, “incident topic clustering”.  
- `mission_or_topic_area` – “communications”, “public affairs”.

### 10.4 Alignment with stakeholder expectations and social impact

- Align actions with stated commitments on sustainability, diversity, and social responsibility.  
- Demonstrate consistent “say–do” alignment to build long‑term credibility.  

**lookup-fields**
- `intended_purpose_and_expected_benefits` – “measure ESG performance”, “monitor DEIA outcomes”, “track social impact”.  
- `ai_system_outputs` – “ESG indicators”, “impact dashboards”, “disparity metrics”.  
- `demographics_used` – used carefully to support fairness/equity analyses.  
- `mission_or_topic_area` – “environment & climate”, “civil rights & equity”, “DEIA”.


