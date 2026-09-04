/* Payment Failure Whisperer — Sandbox Client Logic */

let currentTab = "card";
let currentAmountPaise = 499900;
let lastSimulatedResult = null;

const SCENARIOS = {
  insufficient_funds: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "The customer does not have sufficient funds in the account to complete the payment.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 9995"
  },
  funds_blocked_by_mandate: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "Funds are blocked by an existing mandate.",
    amount: 1850000,
    tab: "card",
    cardNum: "4000 0000 0000 4567"
  },
  transaction_daily_limit_exceeded: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "The customer has exceeded the daily transaction limit set on the card. Some of the cards allow customers to set a limit or have a default limit set.",
    amount: 15000000,
    tab: "card",
    cardNum: "4000 0000 0000 7771"
  },
  transaction_frequency_limit_exceeded: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "NPCI has a transaction limit both on the amount and the frequency per day. Customer has exhausted the frequency limit.",
    amount: 250000,
    tab: "upi",
    vpa: "failure@razorpay"
  },
  authentication_failed: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authentication",
    description: "The payment failed as 3D secure, or OTP authentication failed. This could happen if the user cancels the payment on the authentication (OTP submit) screen or enters incorrect authentication details such as OTP.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 0002"
  },
  incorrect_otp: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authentication",
    description: "The customer has entered an incorrect OTP to complete the payment.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 8882"
  },
  otp_expired: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authentication",
    description: "The OTP has expired.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 8883"
  },
  payment_risk_check_failed: {
    code: "BAD_REQUEST_ERROR",
    source: "bank",
    step: "payment_authorization",
    description: "Payment declined due to risk checks. Risk checks are performed by Razorpay, Gateway, and Issuer Bank. The source parameter would give additional clarity where the risk check failed.",
    amount: 999900,
    tab: "card",
    cardNum: "4000 0000 0000 9999"
  },
  incorrect_cvv: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "The customer has entered an incorrect CVV to complete the payment.",
    amount: 499900,
    tab: "card",
    cvv: "000"
  },
  card_expired: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "The card has expired.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 0069",
    expiry: "01/22"
  },
  debit_instrument_blocked: {
    code: "BAD_REQUEST_ERROR",
    source: "bank",
    step: "payment_authorization",
    description: "The customer is using a blocked card to complete the payment. The card could have been blocked by the issuer or by customers themselves.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 0005"
  },
  card_not_enrolled: {
    code: "BAD_REQUEST_ERROR",
    source: "bank",
    step: "payment_authentication",
    description: "The card is not enrolled for this payment method.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 9991"
  },
  international_transaction_not_allowed: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "International transactions are not allowed.",
    amount: 499900,
    tab: "card",
    cardNum: "5104 0155 5555 5558"
  },
  invalid_vpa: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_initiation",
    description: "The customer has entered an incorrect VPA to complete the payment.",
    amount: 499900,
    tab: "upi",
    vpa: "invalid_handle@nonexistent"
  },
  upi_app_technical_error: {
    code: "GATEWAY_ERROR",
    source: "gateway",
    step: "payment_authorization",
    description: "Technical error occurred at the customer’s PSP due to which the payment failed.",
    amount: 499900,
    tab: "upi",
    vpa: "failure@razorpay"
  },
  payment_timed_out: {
    code: "BAD_REQUEST_ERROR",
    source: "customer",
    step: "payment_authorization",
    description: "The customer did not complete the transaction within the specified time. This error may also happen when no response is received from the gateway.",
    amount: 499900,
    tab: "upi",
    vpa: "timeout@razorpay"
  },
  bank_technical_error: {
    code: "GATEWAY_ERROR",
    source: "bank",
    step: "payment_authorization",
    description: "The issuing bank was facing technical problems at the moment the payment was attempted. This usually occurs when the Core Banking System encounters a technical error while processing the payment.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 0119"
  },
  bank_cutoff_in_progress: {
    code: "GATEWAY_ERROR",
    source: "bank",
    step: "payment_authorization",
    description: "Bank CBS cutoff is in progress. This is a periodic event at the bank's end.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 1111"
  },
  server_error: {
    code: "SERVER_ERROR",
    source: "razorpay",
    step: "payment_authorization",
    description: "Technical error at Razorpay’s server. This usually occurs when there is some server issue at Razorpay’s end.",
    amount: 499900,
    tab: "card",
    cardNum: "4000 0000 0000 5000"
  },
  amount_less_than_minimum_amount: {
    code: "BAD_REQUEST_ERROR",
    source: "business",
    step: "payment_initiation",
    description: "Amount in the payment request is less than the minimum amount. Transacting through some banks have fixed fees. If the payment amount is less than the fixed fee then this error shows up.",
    amount: 50,
    tab: "upi",
    vpa: "customer@upi"
  }
};

function switchTab(tab) {
  currentTab = tab;
  const cardBtn = document.getElementById("tabCardBtn");
  const upiBtn = document.getElementById("tabUpiBtn");
  const cardContainer = document.getElementById("cardFormContainer");
  const upiContainer = document.getElementById("upiFormContainer");

  if (tab === "card") {
    cardBtn.classList.add("active");
    upiBtn.classList.remove("active");
    cardContainer.style.display = "block";
    upiContainer.style.display = "none";
  } else {
    upiBtn.classList.add("active");
    cardBtn.classList.remove("active");
    cardContainer.style.display = "none";
    upiContainer.style.display = "block";
  }
}

function setVpa(vpa) {
  document.getElementById("upiVpa").value = vpa;
  const reason = document.getElementById("scenarioSelector").value;
  const sc = SCENARIOS[reason] || SCENARIOS.insufficient_funds;
  resetScenarioState(reason, sc);
}

function updateAmountDisplay(rupees) {
  const formatted = "₹" + rupees.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  document.getElementById("amountDisplay").textContent = formatted;
  document.getElementById("btnAmount").textContent = formatted;
}

function resetScenarioState(reason, sc) {
  const idleState = document.getElementById("idleState");
  const processingState = document.getElementById("processingState");
  const resultState = document.getElementById("resultState");
  const smsEmptyState = document.getElementById("smsEmptyState");
  const smsIncomingState = document.getElementById("smsIncomingState");
  const smsBubble = document.getElementById("smsBubble");
  const payBtn = document.getElementById("payBtn");

  // Reset intelligence cards to idle
  if (resultState) resultState.style.display = "none";
  if (processingState) processingState.style.display = "none";
  if (idleState) {
    idleState.style.display = "block";
    const idleTitle = document.getElementById("idleTitle");
    const idleSub = document.getElementById("idleSubtitle");
    if (idleTitle) idleTitle.textContent = `Scenario Ready: ${reason}`;
    if (idleSub && sc) {
      idleSub.innerHTML = `Primed failure event: <strong>${sc.code}</strong> (${sc.source} • ${sc.step}). Click <strong>Authorize Payment</strong> below to trigger the gateway simulation and real-time AI diagnostics.`;
    }
  }

  // Clear phone mockup immediately — FIX FOR STALE-STATE SMS BUG
  if (smsBubble) smsBubble.style.display = "none";
  if (smsIncomingState) smsIncomingState.style.display = "none";
  if (smsEmptyState) smsEmptyState.style.display = "flex";

  // Reset Pay button
  if (payBtn) {
    payBtn.disabled = false;
    const formattedAmt = "₹" + (sc.amount / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    payBtn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
      <span>Authorize Payment</span>
      <span id="btnAmount">${formattedAmt}</span>
    `;
  }

  // Hide Before / After button whenever parameters are changed/reset
  const floatingCompareBtn = document.getElementById("floatingCompareBtn");
  if (floatingCompareBtn) {
    floatingCompareBtn.style.display = "none";
  }
}

function onScenarioChange() {
  const reason = document.getElementById("scenarioSelector").value;
  const sc = SCENARIOS[reason];
  if (!sc) return;

  document.getElementById("metaReason").textContent = reason;
  document.getElementById("metaSource").textContent = sc.source;

  currentAmountPaise = sc.amount;
  updateAmountDisplay(sc.amount / 100);

  // Instantly clear any old result and stale SMS preview
  resetScenarioState(reason, sc);

  if (sc.tab === "upi") {
    switchTab("upi");
    if (sc.vpa) document.getElementById("upiVpa").value = sc.vpa;
  } else {
    switchTab("card");
    if (sc.cardNum) document.getElementById("cardNumber").value = sc.cardNum;
    if (sc.expiry) document.getElementById("cardExpiry").value = sc.expiry;
    if (sc.cvv) document.getElementById("cardCvv").value = sc.cvv;
  }
}

async function executeSimulatedPayment() {
  const payBtn = document.getElementById("payBtn");
  const idleState = document.getElementById("idleState");
  const processingState = document.getElementById("processingState");
  const resultState = document.getElementById("resultState");
  const smsEmptyState = document.getElementById("smsEmptyState");
  const smsIncomingState = document.getElementById("smsIncomingState");
  const smsBubble = document.getElementById("smsBubble");

  const pipeStep1 = document.getElementById("pipeStep1");
  const pipeStep2 = document.getElementById("pipeStep2");
  const pipeStep3 = document.getElementById("pipeStep3");
  const stepperTitle = document.getElementById("stepperTitle");
  const stepperSub = document.getElementById("stepperSub");

  // Operator selection
  const reason = document.getElementById("scenarioSelector").value;
  const sc = SCENARIOS[reason] || SCENARIOS.insufficient_funds;

  // Gather payload details
  const method = currentTab;
  const phone = document.getElementById("customerPhone").value;
  const email = document.getElementById("customerEmail").value;
  const vpa = method === "upi" ? document.getElementById("upiVpa").value : "";
  const cardLast4 = method === "card" ? document.getElementById("cardNumber").value.replace(/\s+/g, "").slice(-4) : "";

  // Enter processing state
  payBtn.disabled = true;
  payBtn.innerHTML = `<span>Authorizing via Gateway...</span>`;
  idleState.style.display = "none";
  resultState.style.display = "none";
  processingState.style.display = "block";

  // Phone: transition from empty to incoming alert indicator
  if (smsEmptyState) smsEmptyState.style.display = "none";
  if (smsBubble) smsBubble.style.display = "none";
  if (smsIncomingState) smsIncomingState.style.display = "flex";

  // Pipeline Stepper: Stage 1 Ingestion
  if (pipeStep1) pipeStep1.className = "pipeline-step active";
  if (pipeStep2) pipeStep2.className = "pipeline-step";
  if (pipeStep3) pipeStep3.className = "pipeline-step";
  if (stepperTitle) stepperTitle.textContent = "1. Dispatching to Razorpay Gateway...";
  if (stepperSub) stepperSub.textContent = `Validating ${method.toUpperCase()} instrument & initiating authorization`;

  // Start animated progression
  const stepTimer1 = setTimeout(() => {
    if (pipeStep1) pipeStep1.className = "pipeline-step done";
    if (pipeStep2) pipeStep2.className = "pipeline-step active";
    if (stepperTitle) stepperTitle.textContent = "2. Issuer Bank Core Banking System (CBS)...";
    if (stepperSub) stepperSub.textContent = `Bank authorization declined: ${reason}`;
  }, 220);

  const stepTimer2 = setTimeout(() => {
    if (pipeStep2) pipeStep2.className = "pipeline-step done";
    if (pipeStep3) pipeStep3.className = "pipeline-step active";
    if (stepperTitle) stepperTitle.textContent = "3. Payment Failure Whisperer AI Intercepting...";
    if (stepperSub) stepperSub.textContent = "Synthesizing plain-English explanation & SMS dispatch";
  }, 500);

  try {
    const response = await fetch("/api/simulate-payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: reason,
        error_code: sc.code,
        error_source: sc.source,
        error_step: sc.step,
        error_description: sc.description,
        amount: currentAmountPaise,
        currency: "INR",
        method: method,
        email: email,
        contact: phone,
        card_network: "Visa",
        card_issuer: "HDFC",
        card_type: "debit",
        card_last4: cardLast4 || "4321",
        vpa: vpa
      })
    });

    clearTimeout(stepTimer1);
    clearTimeout(stepTimer2);

    const data = await response.json();

    // Finalize pipeline steps
    if (pipeStep1) pipeStep1.className = "pipeline-step done";
    if (pipeStep2) pipeStep2.className = "pipeline-step done";
    if (pipeStep3) pipeStep3.className = "pipeline-step done";

    // Render gateway failure
    document.getElementById("resultErrorCode").textContent = data.error_code || sc.code;
    document.getElementById("resultErrorDescription").textContent = sc.description;

    // Render AI Whisperer guidance
    document.getElementById("resultExplanation").textContent = data.explanation;
    document.getElementById("resultRetryWindow").textContent = "Window: " + (data.estimated_retry_window || "Instant");
    document.getElementById("resultSource").textContent = data.source === "groq" ? ("Groq (" + (data.model || "compound-mini") + ")") : "Rule Engine Fallback";
    document.getElementById("resultLatency").textContent = (data.latency_ms || 120) + "ms";
    document.getElementById("resultConfidence").textContent = Math.round((data.confidence_score || 0.98) * 100) + "%";

    // Populate recovery actions list
    const actionsContainer = document.getElementById("resultActionsList");
    actionsContainer.innerHTML = "";
    if (data.recovery_actions && data.recovery_actions.length > 0) {
      data.recovery_actions.forEach(action => {
        const item = document.createElement("div");
        item.className = "action-card";
        item.innerHTML = `
          <div class="action-card-header">
            <span class="action-step-badge">${actionsContainer.children.length + 1}</span>
            <span class="action-label">${escapeHtml(action.label || 'Action')}</span>
          </div>
          <div class="action-desc">${escapeHtml(action.description || '')}</div>
        `;
        actionsContainer.appendChild(item);
      });
    }

    // Deliver SMS to phone mockup
    const phoneAmount = "₹" + (currentAmountPaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 });
    document.getElementById("smsMessageText").textContent = 
      `Alert: Your ${phoneAmount} payment did not go through. Reason: ${data.explanation}`;
    
    const recoveryLink = document.getElementById("smsRecoveryLink");
    recoveryLink.href = data.recovery_url || "#";
    recoveryLink.textContent = "Tap to retry: " + (data.recovery_url || "http://127.0.0.1:5000/retry/...");

    const now = new Date();
    document.getElementById("smsTimestamp").textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Transition phone mockup to delivered SMS
    if (smsIncomingState) smsIncomingState.style.display = "none";
    if (smsBubble) smsBubble.style.display = "block";

    // Show result state
    processingState.style.display = "none";
    resultState.style.display = "block";

    // Store completed simulation context for dynamic Before / After modal
    lastSimulatedResult = {
      reason: reason,
      sc: sc,
      data: data,
      amountPaise: currentAmountPaise
    };

    // Reveal floating Before / After trigger button only after simulation completes
    const floatingCompareBtn = document.getElementById("floatingCompareBtn");
    if (floatingCompareBtn) {
      floatingCompareBtn.style.display = "inline-flex";
    }

  } catch (err) {
    console.error("Simulation request failed:", err);
    alert("Error executing payment simulation: " + err.message);
    processingState.style.display = "none";
    idleState.style.display = "block";
    if (smsIncomingState) smsIncomingState.style.display = "none";
    if (smsEmptyState) smsEmptyState.style.display = "flex";
  } finally {
    payBtn.disabled = false;
    const formatted = "₹" + (currentAmountPaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    payBtn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
      <span>Authorize Payment</span>
      <span id="btnAmount">${formatted}</span>
    `;
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* --------------------------------------------------------------------------
   Dynamic Before vs After Comparison Matrix Logic (All 20 Razorpay Errors)
   -------------------------------------------------------------------------- */
const SCENARIO_PSYCHOLOGY = {
  insufficient_funds: {
    dropoff: "~78% Cart Drop-off",
    recovery: "+42% Recovered GMV",
    recoveryShort: "+42%",
    friction: [
      'High anxiety: Customer wonders <em>"Did my bank account get debited anyway?"</em>',
      'Embarrassment & silence: Generic decline leaves customer confused without alternatives.',
      'Immediate abandonment: Customer closes the tab or switches to a competitor.'
    ],
    delight: [
      'Immediate reassurance: Explicitly confirms ₹0 was debited from account.',
      'Frictionless 1-tap route: Seamlessly switch to liquid UPI (GPay/PhonePe).',
      'Omnichannel recovery: Preserves order with an SMS retry token valid for 60m.'
    ]
  },
  funds_blocked_by_mandate: {
    dropoff: "~85% Cart Drop-off",
    recovery: "+46% Recovered GMV",
    recoveryShort: "+46%",
    friction: [
      'Deep confusion: Customer does not understand what a "mandate hold" means.',
      'Account freeze fear: Customer panics assuming their bank account is locked.',
      'Total checkout drop-off: Reluctance to attempt any other payment.'
    ],
    delight: [
      'Regulatory clarity: Explains RBI ₹15,000 auto-debit hold in plain English.',
      'Mandate bypass routing: Guides customer to credit cards or unencumbered accounts.',
      'Zero merchant support tickets: Prevents anxious chargeback inquiries.'
    ]
  },
  transaction_daily_limit_exceeded: {
    dropoff: "~74% Cart Drop-off",
    recovery: "+36% Recovered GMV",
    recoveryShort: "+36%",
    friction: [
      'Perplexity: Customer has sufficient balance but transaction is rejected blindly.',
      'Repeated retry hazard: Repeated attempts risk temporary card security lock.',
      'Checkout abandonment: Customer leaves without understanding card limits.'
    ],
    delight: [
      'Transparent limit diagnosis: Clarifies daily spend limit without blaming user.',
      'Alternate instrument routing: Suggests UPI, Netbanking, or alternate card.',
      'Bank app toggle guide: Informs how to increase card limit in banking app.'
    ]
  },
  transaction_frequency_limit_exceeded: {
    dropoff: "~70% Cart Drop-off",
    recovery: "+40% Recovered GMV",
    recoveryShort: "+40%",
    friction: [
      'Cryptic regulatory rule: Customer unaware of NPCI daily UPI transaction count limits.',
      'UPI retry loop: Repeated attempts via the same UPI app continue failing.',
      'Checkout frustration: Customer gives up and exits site.'
    ],
    delight: [
      'NPCI velocity education: Explains daily transaction frequency cap clearly.',
      'Channel switch: Offers instant 1-click fallback to Debit/Credit Card or Netbanking.',
      'Frictionless resumption: Order preserved without re-entering checkout details.'
    ]
  },
  authentication_failed: {
    dropoff: "~80% Cart Drop-off",
    recovery: "+45% Recovered GMV",
    recoveryShort: "+45%",
    friction: [
      'Security paranoia: Customer fears 3DS authentication gateway was intercepted.',
      'Cryptic AUTH_FAILED: No explanation whether OTP or bank password failed.',
      'Immediate exit: Customer distrusts checkout security.'
    ],
    delight: [
      'Transparent explanation: Clarifies 3D Secure / OTP cancellation cleanly.',
      'Safe re-trigger: Generates a fresh secure OTP authentication window.',
      'Biometric UPI fallback: Seamlessly switch to biometric UPI push approval.'
    ]
  },
  incorrect_otp: {
    dropoff: "~65% Cart Drop-off",
    recovery: "+48% Recovered GMV",
    recoveryShort: "+48%",
    friction: [
      'Typo frustration: Customer cannot tell if digits were wrong or server glitched.',
      'Dread of lockout: Fear that further attempts will lock card for 24 hours.',
      'Session timeout: Losing filled order details and needing to start from scratch.'
    ],
    delight: [
      'Direct diagnosis: Explicitly highlights OTP mismatch so customer checks latest SMS.',
      'Fresh OTP generation: 1-click resend without resetting cart state.',
      'Push notification switch: Option to approve payment via UPI app instead of SMS.'
    ]
  },
  otp_expired: {
    dropoff: "~68% Cart Drop-off",
    recovery: "+44% Recovered GMV",
    recoveryShort: "+44%",
    friction: [
      'Telco delay penalty: Customer penalized because bank SMS arrived late.',
      'Silent failure: Error code gives no clue that OTP was expired.',
      'Order abandonment: Customer assumes merchant payment gateway is broken.'
    ],
    delight: [
      'Telco latency empathy: Explains SMS validity window expired harmlessly.',
      'Instant resend trigger: Automatically requests a fresh OTP immediately.',
      'UPI Intent push: Bypasses SMS dependencies entirely via app intent.'
    ]
  },
  payment_risk_check_failed: {
    dropoff: "~88% Cart Drop-off",
    recovery: "+32% Recovered GMV",
    recoveryShort: "+32%",
    friction: [
      'Offense and distrust: Customer feels falsely flagged as fraudulent.',
      'Zero transparency: No clarity on whether bank, gateway, or merchant rejected.',
      'Brand reputation damage: Customer vows never to purchase from merchant again.'
    ],
    delight: [
      'Respectful explanation: Notes automated safety check without accusatory tone.',
      'Verified channel guidance: Suggests 3DS-verified UPI or trusted domestic card.',
      'Bank assistance tips: Steps to verify legitimate activity with issuer bank.'
    ]
  },
  incorrect_cvv: {
    dropoff: "~62% Cart Drop-off",
    recovery: "+52% Recovered GMV",
    recoveryShort: "+52%",
    friction: [
      'Vague BAD_REQUEST: Customer cannot tell if card number, expiry, or CVV failed.',
      'Repetitive re-entry: Re-typing all 16 card numbers from scratch in annoyance.',
      'Cart drop-off: Customer leaves checkout to find physical card.'
    ],
    delight: [
      'Pinpoint field identification: Identifies CVV specifically without exposing data.',
      'Preserved card details: Keeps card details intact so customer only corrects 3 digits.',
      'Visual guide: Explains the 3-digit security code on card reverse.'
    ]
  },
  card_expired: {
    dropoff: "~75% Cart Drop-off",
    recovery: "+38% Recovered GMV",
    recoveryShort: "+38%",
    friction: [
      'Surprise decline: Customer rarely tracks exact expiration month on older cards.',
      'Repetitive attempts: Trying expired card again results in issuer decline.',
      'Cart abandonment: Customer leaves to search for new replacement card.'
    ],
    delight: [
      'Gentle card reminder: Informs customer that card validity period has lapsed.',
      'One-tap UPI fallback: Pay immediately using phone UPI without physical card.',
      'Saved token update: Seamless prompt to save replacement card for future orders.'
    ]
  },
  debit_instrument_blocked: {
    dropoff: "~82% Cart Drop-off",
    recovery: "+34% Recovered GMV",
    recoveryShort: "+34%",
    friction: [
      'Alarm & panic: Customer fears card theft or administrative account freeze.',
      'Zero guidance: No clue whether block is temporary or user-toggled.',
      'Support desk surge: Anxious customer calls merchant support in distress.'
    ],
    delight: [
      'Issuer block clarity: Distinguishes between bank app freeze and card issues.',
      'Mobile app unfreeze tip: Guides customer to check "Card Controls" in bank app.',
      'Alternative payment route: Instant fallback to UPI or secondary bank card.'
    ]
  },
  card_not_enrolled: {
    dropoff: "~76% Cart Drop-off",
    recovery: "+39% Recovered GMV",
    recoveryShort: "+39%",
    friction: [
      'Baffling rejection: Valid bank card rejected as "not enrolled" without explanation.',
      'Blames checkout: Customer assumes merchant software has compatibility bugs.',
      'Competitor switch: Leaves to buy from another store.'
    ],
    delight: [
      'Enrollment education: Explains online e-commerce transaction toggle requirement.',
      'Quick enablement steps: Guides to activate e-commerce toggle in mobile banking.',
      'Direct payment alternatives: Instant switch to UPI or Netbanking.'
    ]
  },
  international_transaction_not_allowed: {
    dropoff: "~79% Cart Drop-off",
    recovery: "+41% Recovered GMV",
    recoveryShort: "+41%",
    friction: [
      'RBI rule ignorance: Customer does not know RBI mandates international card opt-in.',
      'Repeated card declines: Customer keeps retrying foreign or non-INR payment.',
      'Cart abandonment: Customer assumes merchant does not accept their card.'
    ],
    delight: [
      'RBI compliance insight: Explains RBI regulation requiring explicit customer opt-in.',
      'Banking app path: Step-by-step path: Mobile App -> Card Controls -> International.',
      'Domestic INR option: Pay via RuPay or domestic UPI instantly.'
    ]
  },
  invalid_vpa: {
    dropoff: "~60% Cart Drop-off",
    recovery: "+55% Recovered GMV",
    recoveryShort: "+55%",
    friction: [
      'Typo blindness: Customer missed a letter in `@okhdfcbank` or `@paytm`.',
      'Silent failure: Gateway error gives no clue whether VPA or bank was at fault.',
      'Checkout abandonment: Closes tab thinking merchant UPI gateway is down.'
    ],
    delight: [
      'Handle diagnosis: Identifies incorrect UPI ID format immediately.',
      'Common handle suggestions: Auto-suggests @okaxis, @okhdfcbank, @ybl handles.',
      'QR code fallback: Offer instant QR code scan so typing handle is eliminated.'
    ]
  },
  upi_app_technical_error: {
    dropoff: "~71% Cart Drop-off",
    recovery: "+43% Recovered GMV",
    recoveryShort: "+43%",
    friction: [
      'PSP outage confusion: Customer does not know if GPay, PhonePe, or bank is down.',
      'Multiple debit fear: Customer checks bank app repeatedly fearing money lost.',
      'Abandons purchase: Customer exits checkout to wait until later.'
    ],
    delight: [
      'Customer reassurance: Confirms money is completely untouched in bank account.',
      'Cross-PSP suggestion: Suggests switching from PhonePe to Paytm or GPay.',
      'Smart retry countdown: Recommends retry in 5 minutes once PSP queue clears.'
    ]
  },
  payment_timed_out: {
    dropoff: "~66% Cart Drop-off",
    recovery: "+47% Recovered GMV",
    recoveryShort: "+47%",
    friction: [
      'Pending state anxiety: Did payment complete right at timeout?',
      'Fear of double-charge: Customer afraid to click pay again.',
      'Lost cart: Re-entering items from scratch causes frustration.'
    ],
    delight: [
      'Timeout exoneration: Confirms gateway session expired with zero deduction.',
      'One-click session revival: Restores exact cart with a fresh session timer.',
      'Faster payment route: Suggests UPI Intent push for instant 5-second completion.'
    ]
  },
  bank_technical_error: {
    dropoff: "~83% Cart Drop-off",
    recovery: "+37% Recovered GMV",
    recoveryShort: "+37%",
    friction: [
      'Terrifying error: Customer fears bank Core Banking System crashed mid-transit.',
      'Repeated retries: Retrying against a down CBS risks locking account.',
      'Abandoned purchase: Unwilling to try merchant again today.'
    ],
    delight: [
      'Bank exoneration: Clarifies bank CBS outage, confirming customer is not at fault.',
      'Alternate bank routing: Suggests an instrument on a different banking network.',
      'Automated SMS recovery: Sends 1-click recovery link when bank CBS stabilizes.'
    ]
  },
  bank_cutoff_in_progress: {
    dropoff: "~81% Cart Drop-off",
    recovery: "+35% Recovered GMV",
    recoveryShort: "+35%",
    friction: [
      'Cryptic midnight failure: Customer shopping at night faces unexplained rejection.',
      'Confusion: Card worked hours earlier; customer suspects compromised account.',
      'Permanent drop-off: Customer leaves and forgets order.'
    ],
    delight: [
      'Plain-English cutoff explanation: Informs of nightly bank batch settlement window.',
      'Instant bypass: Suggests UPI or Private Bank card unaffected by cutoff.',
      'Scheduled retry link: Preserves order with an SMS alert once cutoff window passes.'
    ]
  },
  server_error: {
    dropoff: "~86% Cart Drop-off",
    recovery: "+33% Recovered GMV",
    recoveryShort: "+33%",
    friction: [
      'Gateway crash fear: Customer assumes payment gateway crashed during charge.',
      'Doubt about debit: Customer fears money debited without acknowledgment.',
      'Anger at merchant: Blames merchant for unstable checkout software.'
    ],
    delight: [
      'Reassurance & transparency: Confirms ₹0 was deducted from customer account.',
      'Secondary route fallback: Automatically retries via redundant bank gateway.',
      'Direct SMS link: Sends secure recovery link so customer does not lose order.'
    ]
  },
  amount_less_than_minimum_amount: {
    dropoff: "~58% Cart Drop-off",
    recovery: "+60% Recovered GMV",
    recoveryShort: "+60%",
    friction: [
      'Baffling error: Customer does not understand why small amount is rejected.',
      'Technical jargon: "AMOUNT_LESS_THAN_MINIMUM" looks like a software bug.',
      'Cart abandoned: Customer cancels checkout in frustration.'
    ],
    delight: [
      'Transparent minimum rule: Explains gateway fixed-fee minimum threshold.',
      'UPI micro-payment route: Advises UPI which natively supports low amounts.',
      'Clean explanation: Clear, friendly advice to complete purchase.'
    ]
  }
};

function getScenarioPsychology(reason, sc) {
  if (SCENARIO_PSYCHOLOGY[reason]) {
    return SCENARIO_PSYCHOLOGY[reason];
  }
  return {
    dropoff: "~72% Cart Drop-off",
    recovery: "+38% Recovered GMV",
    recoveryShort: "+38%",
    friction: [
      'High anxiety: Customer wonders "Did my money get debited?"',
      'Cryptic error code: No recovery pathway or alternative method offered.',
      'Cart abandonment: Customer closes tab or switches to competitor.'
    ],
    delight: [
      'Immediate reassurance: Explicitly confirms no money was debited.',
      'Frictionless 1-click retry: Seamlessly switch to UPI or alternate instrument.',
      'Omnichannel recovery: Complete order via mobile link anytime within 60 mins.'
    ]
  };
}

function openBeforeAfterModal() {
  const modal = document.getElementById("beforeAfterModal");
  if (!modal) return;

  // Fallback to active dropdown scenario if opened before simulation
  if (!lastSimulatedResult) {
    const reason = document.getElementById("scenarioSelector").value;
    const sc = SCENARIOS[reason] || SCENARIOS.insufficient_funds;
    lastSimulatedResult = {
      reason: reason,
      sc: sc,
      data: {
        error_code: sc.code,
        explanation: sc.description,
        recovery_actions: [
          { label: "Retry via UPI", description: "Use GPay, PhonePe, or Paytm" },
          { label: "Use alternate card", description: "Try another credit or debit card" }
        ],
        estimated_retry_window: "Instant",
        latency_ms: 120
      },
      amountPaise: currentAmountPaise
    };
  }

  const { reason, sc, data, amountPaise } = lastSimulatedResult;
  const psych = getScenarioPsychology(reason, sc);

  // Update Dynamic Scenario Context Bar
  const titleEl = document.getElementById("modalScenarioTitle");
  if (titleEl) titleEl.textContent = reason;

  const badgeEl = document.getElementById("modalScenarioSourceBadge");
  if (badgeEl) badgeEl.textContent = `${(sc.source || 'GATEWAY').toUpperCase()} • ${(sc.step || 'PAYMENT_AUTHORIZATION').toUpperCase()}`;

  const orderEl = document.getElementById("modalScenarioOrder");
  if (orderEl) {
    const formatted = "₹" + (amountPaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    orderEl.textContent = `Order #OD-90214 (${formatted})`;
  }

  // Update Column Headers
  const legacyStat = document.getElementById("legacyStatBadge");
  if (legacyStat) legacyStat.textContent = psych.dropoff;

  const whispererStat = document.getElementById("whispererStatBadge");
  if (whispererStat) whispererStat.textContent = psych.recovery;

  // Update Left Column (Legacy Standard Razorpay)
  const legacyCode = document.getElementById("legacyErrorCode");
  if (legacyCode) legacyCode.textContent = data.error_code || sc.code;

  const legacyStep = document.getElementById("legacyErrorStep");
  if (legacyStep) legacyStep.textContent = `step: ${sc.step || 'payment_authorization'}`;

  const legacyDesc = document.getElementById("legacyErrorDesc");
  if (legacyDesc) legacyDesc.textContent = sc.description;

  const f1 = document.getElementById("legacyFriction1");
  if (f1 && psych.friction[0]) f1.innerHTML = psych.friction[0];
  const f2 = document.getElementById("legacyFriction2");
  if (f2 && psych.friction[1]) f2.innerHTML = psych.friction[1];
  const f3 = document.getElementById("legacyFriction3");
  if (f3 && psych.friction[2]) f3.innerHTML = psych.friction[2];

  // Update Right Column (With Failure Whisperer)
  const windowBadge = document.getElementById("whispererRetryWindowBadge");
  if (windowBadge) windowBadge.textContent = "Window: " + (data.estimated_retry_window || "Instant");

  const expText = document.getElementById("whispererExpText");
  if (expText) expText.textContent = `"${data.explanation || sc.description}"`;

  const actionsBox = document.getElementById("whispererActionsBox");
  if (actionsBox) {
    actionsBox.innerHTML = "";
    const actions = (data.recovery_actions && data.recovery_actions.length > 0)
      ? data.recovery_actions
      : [
          { label: "Pay via UPI (GPay/PhonePe)", description: "Switch to liquid bank account." },
          { label: "Use alternate card", description: "Try another debit or credit card." }
        ];

    actions.forEach((act, idx) => {
      const item = document.createElement("div");
      item.className = "whisperer-action-item";
      item.innerHTML = `
        <span class="action-num">${idx + 1}</span>
        <div><strong>${escapeHtml(act.label || 'Action')}</strong> — ${escapeHtml(act.description || '')}</div>
      `;
      actionsBox.appendChild(item);
    });
  }

  const d1 = document.getElementById("whispererDelight1");
  if (d1 && psych.delight[0]) d1.innerHTML = psych.delight[0];
  const d2 = document.getElementById("whispererDelight2");
  if (d2 && psych.delight[1]) d2.innerHTML = psych.delight[1];
  const d3 = document.getElementById("whispererDelight3");
  if (d3 && psych.delight[2]) d3.innerHTML = psych.delight[2];

  // Update Metrics
  const recVal = document.getElementById("whispererRecoveryVal");
  if (recVal) recVal.textContent = psych.recoveryShort || "+38%";

  const latVal = document.getElementById("whispererLatencyVal");
  if (latVal) latVal.textContent = (data.latency_ms || 120) + "ms";

  modal.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeBeforeAfterModal() {
  const modal = document.getElementById("beforeAfterModal");
  if (modal) {
    modal.style.display = "none";
    document.body.style.overflow = "auto";
  }
}

function handleModalBackdropClick(event) {
  if (event.target && event.target.id === "beforeAfterModal") {
    closeBeforeAfterModal();
  }
}

// Bind ESC key to close modal
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeBeforeAfterModal();
  }
});

// Initialize default scenario on page load
document.addEventListener("DOMContentLoaded", () => {
  // Ensure visible URL in browser address bar reflects /zerodrop
  if (window.location.pathname === "/" || window.location.pathname === "/sandbox") {
    try {
      history.replaceState(null, "", "/zerodrop");
    } catch (e) {}
  }
  onScenarioChange();
});
