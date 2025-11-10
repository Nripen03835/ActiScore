// Main application logic
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initApp();
});

function initApp() {
    // Set up event listeners
    setupEventListeners();
    
    // Initialize range value displays
    updateRangeValue('market-size', 'market-size-value');
    updateRangeValue('competition', 'competition-value');
}

function setupEventListeners() {
    // Form submission
    const form = document.getElementById('startup-form');
    form.addEventListener('submit', handleFormSubmit);
    
    // Range input updates
    document.getElementById('market-size').addEventListener('input', function() {
        updateRangeValue('market-size', 'market-size-value');
    });
    
    document.getElementById('competition').addEventListener('input', function() {
        updateRangeValue('competition', 'competition-value');
    });
}

function updateRangeValue(inputId, valueSpanId) {
    const input = document.getElementById(inputId);
    const valueSpan = document.getElementById(valueSpanId);
    valueSpan.textContent = input.value;
}

function handleFormSubmit(event) {
    event.preventDefault();
    
    // Show loading state
    const predictBtn = document.getElementById('predict-btn');
    const originalText = predictBtn.textContent;
    predictBtn.innerHTML = '<span class="loading"></span> Predicting...';
    predictBtn.disabled = true;
    
    // Simulate API call delay
    setTimeout(() => {
        // Get form data
        const formData = getFormData();
        
        // Make prediction (in a real app, this would be an API call)
        const prediction = makePrediction(formData);
        
        // Display results
        displayResults(prediction);
        
        // Update visualizations
        updateCharts(prediction);
        update3DVisualization(prediction);
        
        // Reset button
        predictBtn.textContent = originalText;
        predictBtn.disabled = false;
    }, 1500);
}

function getFormData() {
    return {
        industry: document.getElementById('industry').value,
        funding: parseInt(document.getElementById('funding').value),
        experience: parseInt(document.getElementById('experience').value),
        teamSize: parseInt(document.getElementById('team-size').value),
        marketSize: parseInt(document.getElementById('market-size').value),
        competition: parseInt(document.getElementById('competition').value)
    };
}

// Mock ML prediction function (in a real app, this would call a backend API)
function makePrediction(formData) {
    // This is a simplified mock prediction
    // In reality, this would use a trained XGBoost or RandomForest model
    
    let baseScore = 50; // Base probability
    
    // Adjust based on funding (more funding = higher chance, but with diminishing returns)
    const fundingImpact = Math.min(formData.funding / 1000000, 20); // Cap at 20% increase
    baseScore += fundingImpact;
    
    // Adjust based on experience
    const experienceImpact = Math.min(formData.experience * 2, 15); // Cap at 15% increase
    baseScore += experienceImpact;
    
    // Adjust based on team size (optimal around 5-15)
    let teamImpact = 0;
    if (formData.teamSize >= 5 && formData.teamSize <= 15) {
        teamImpact = 10;
    } else if (formData.teamSize > 15) {
        teamImpact = -5; // Too large teams can be inefficient
    } else {
        teamImpact = -10; // Too small teams lack resources
    }
    baseScore += teamImpact;
    
    // Adjust based on market size
    const marketImpact = (formData.marketSize - 5) * 3; // Scale of 1-10, 5 is neutral
    baseScore += marketImpact;
    
    // Adjust based on competition
    const competitionImpact = (5 - formData.competition) * 2; // Less competition is better
    baseScore += competitionImpact;
    
    // Industry adjustments
    const industryMultipliers = {
        'tech': 1.1,
        'healthcare': 1.05,
        'finance': 1.0,
        'ecommerce': 0.95,
        'education': 0.9,
        'other': 0.85
    };
    
    const industryMultiplier = industryMultipliers[formData.industry] || 1.0;
    baseScore *= industryMultiplier;
    
    // Ensure probability is between 0 and 100
    const probability = Math.max(0, Math.min(100, baseScore));
    
    // Determine risk level
    let riskLevel;
    if (probability >= 70) {
        riskLevel = 'Low';
    } else if (probability >= 40) {
        riskLevel = 'Medium';
    } else {
        riskLevel = 'High';
    }
    
    // Generate insights
    const insights = generateInsights(formData, probability);
    
    // Generate forecast data
    const forecast = generateForecast(formData, probability);
    
    return {
        probability: Math.round(probability),
        riskLevel: riskLevel,
        insights: insights,
        forecast: forecast
    };
}

function generateInsights(formData, probability) {
    const insights = [];
    
    // Funding insight
    if (formData.funding < 100000) {
        insights.push("Consider seeking additional funding to support growth initiatives.");
    } else if (formData.funding > 1000000) {
        insights.push("Strong funding position provides runway for strategic experiments.");
    } else {
        insights.push("Adequate funding level for initial operations and market testing.");
    }
    
    // Experience insight
    if (formData.experience < 3) {
        insights.push("Founder experience is limited; consider adding advisors with industry expertise.");
    } else if (formData.experience > 10) {
        insights.push("Strong founder experience increases credibility with investors and customers.");
    } else {
        insights.push("Founder experience is adequate for navigating early-stage challenges.");
    }
    
    // Team size insight
    if (formData.teamSize < 5) {
        insights.push("Small team may struggle with workload; consider strategic hiring.");
    } else if (formData.teamSize > 20) {
        insights.push("Large team requires strong management to maintain efficiency.");
    } else {
        insights.push("Team size is optimal for agility and capability balance.");
    }
    
    // Market size insight
    if (formData.marketSize >= 8) {
        insights.push("Large target market provides significant growth potential.");
    } else if (formData.marketSize <= 3) {
        insights.push("Niche market requires precise targeting and efficient customer acquisition.");
    } else {
        insights.push("Moderate market size offers balanced opportunity and competition.");
    }
    
    // Competition insight
    if (formData.competition >= 8) {
        insights.push("High competition requires strong differentiation and value proposition.");
    } else if (formData.competition <= 3) {
        insights.push("Low competition suggests potential market opportunity or validation needed.");
    } else {
        insights.push("Moderate competition indicates healthy market with proven demand.");
    }
    
    // Overall probability insight
    if (probability >= 70) {
        insights.push("Strong indicators for success; focus on execution and scaling.");
    } else if (probability >= 40) {
        insights.push("Promising venture with areas for improvement; iterate based on market feedback.");
    } else {
        insights.push("Significant challenges identified; consider pivoting strategy or strengthening team.");
    }
    
    return insights;
}

function generateForecast(formData, probability) {
    // Generate mock forecast data for 12 months
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const revenue = [];
    const profit = [];
    const loss = [];
    
    // Base values influenced by probability and funding
    const baseRevenue = formData.funding * 0.1 * (probability / 100);
    const baseGrowth = 1 + (probability / 500); // Monthly growth rate
    
    let currentRevenue = baseRevenue;
    
    for (let i = 0; i < 12; i++) {
        // Add some randomness to make it more realistic
        const randomFactor = 0.8 + Math.random() * 0.4;
        currentRevenue = currentRevenue * baseGrowth * randomFactor;
        
        revenue.push(Math.round(currentRevenue));
        
        // Profit/loss calculations (simplified)
        const expenses = formData.funding / 24; // Fixed monthly expenses
        const net = currentRevenue - expenses;
        
        if (net > 0) {
            profit.push(Math.round(net));
            loss.push(0);
        } else {
            profit.push(0);
            loss.push(Math.round(Math.abs(net)));
        }
    }
    
    return {
        months: months,
        revenue: revenue,
        profit: profit,
        loss: loss
    };
}

function displayResults(prediction) {
    // Show results section
    const resultsSection = document.getElementById('results');
    resultsSection.style.display = 'block';
    
    // Update probability
    document.getElementById('probability-value').textContent = `${prediction.probability}%`;
    
    // Update risk level
    const riskElement = document.getElementById('risk-level');
    riskElement.textContent = prediction.riskLevel;
    riskElement.className = ''; // Clear previous classes
    riskElement.classList.add(`risk-${prediction.riskLevel.toLowerCase()}`);
    
    // Update insights
    const insightsList = document.getElementById('insights-list');
    insightsList.innerHTML = '';
    
    prediction.insights.forEach(insight => {
        const li = document.createElement('li');
        li.textContent = insight;
        insightsList.appendChild(li);
    });
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}