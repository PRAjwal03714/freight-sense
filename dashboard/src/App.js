import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { Newspaper, Search } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  // State management
  const [routes, setRoutes] = useState({ origins: [], destinations: [] });
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch available routes on mount
  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/routes`)
      .then(response => {
        setRoutes(response.data);
        setOrigin(response.data.origins[0]);
        setDestination(response.data.destinations[3]); // Default to 4th option
      })
      .catch(err => console.error('Failed to fetch routes:', err));
  }, []);

  // Generate risk explanation
  const explainRisk = async () => {
    if (!origin || !destination) {
      setError('Please select both origin and destination');
      return;
    }

    if (origin === destination) {
      setError('Origin and destination must be different');
      return;
    }

    setLoading(true);
    setError(null);
    setExplanation(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/explain`, {
        origin,
        destination
      });
      setExplanation(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate explanation');
    } finally {
      setLoading(false);
    }
  };

  // Risk score color
  const getRiskColor = (score) => {
    if (score >= 70) return 'text-red-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRiskBgColor = (score) => {
    if (score >= 70) return 'bg-red-100 border-red-300';
    if (score >= 50) return 'bg-yellow-100 border-yellow-300';
    return 'bg-green-100 border-green-300';
  };

  const getRiskLabel = (score) => {
    if (score >= 70) return 'HIGH RISK';
    if (score >= 50) return 'MODERATE';
    return 'LOW RISK';
  };

  // Prepare forecast chart data
  const getForecastData = () => {
    if (!explanation?.forecast) return [];
    return [
      { horizon: '7-day', delay: explanation.forecast['7_day'] },
      { horizon: '14-day', delay: explanation.forecast['14_day'] },
      { horizon: '30-day', delay: explanation.forecast['30_day'] }
    ];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                FreightSense
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                AI-Powered Supply Chain Risk Intelligence
              </p>
            </div>
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>API Connected</span>
              </div>
              <div className="bg-slate-700 px-3 py-1 rounded-lg">
                v1.0.0
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Route Selection */}
        <div className="bg-slate-800 rounded-xl shadow-xl p-8 mb-8 border border-slate-700">
          <h2 className="text-xl font-semibold mb-6 text-slate-200">
            Select Route
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Origin Port
              </label>
              <select
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              >
                {routes.origins.map((port) => (
                  <option key={port} value={port}>{port}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Destination Port
              </label>
              <select
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              >
                {routes.destinations.map((port) => (
                  <option key={port} value={port}>{port}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={explainRisk}
                disabled={loading}
                className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 disabled:from-slate-600 disabled:to-slate-600 rounded-lg font-semibold transition shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  'Explain Risk'
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-900 bg-opacity-50 border border-red-500 rounded-lg text-red-200">
              ⚠️ {error}
            </div>
          )}
        </div>

        {/* Results */}
        {explanation && (
          <div className="space-y-6">
            {/* Risk Score Card */}
            <div className={`${getRiskBgColor(explanation.risk_score)} rounded-xl shadow-xl p-8 border-2`}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-slate-800">
                  Risk Assessment
                </h2>
                <span className={`${getRiskColor(explanation.risk_score)} text-sm font-bold px-4 py-2 bg-white rounded-lg shadow`}>
                  {getRiskLabel(explanation.risk_score)}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-slate-800">
                <div>
                  <div className="text-5xl font-bold mb-2">
                    {explanation.risk_score}
                    <span className="text-2xl text-slate-600">/100</span>
                  </div>
                  <div className="w-full bg-slate-300 rounded-full h-3 mt-2">
                    <div
                      className={`h-3 rounded-full ${explanation.risk_score >= 70 ? 'bg-red-600' : explanation.risk_score >= 50 ? 'bg-yellow-600' : 'bg-green-600'}`}
                      style={{ width: `${explanation.risk_score}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-slate-600 mb-1">7-Day Forecast</p>
                  <p className="text-3xl font-bold">
                    +{explanation.forecast['7_day']} days
                  </p>
                  <p className="text-sm text-slate-600 mt-1">delay expected</p>
                </div>

                <div>
                  <p className="text-sm text-slate-600 mb-1">Confidence</p>
                  <p className="text-3xl font-bold">
                    {Math.round(explanation.confidence * 100)}%
                  </p>
                  <p className="text-sm text-slate-600 mt-1">prediction accuracy</p>
                </div>
              </div>
            </div>

            {/* Weather Conditions */}
            <div className="bg-slate-800 rounded-xl shadow-xl p-8 border border-slate-700">
              <h3 className="text-xl font-semibold mb-6 flex items-center text-slate-200">
                <span className="text-2xl mr-3">🌧️</span>
                Weather Conditions
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                  <p className="text-slate-400 text-sm mb-2">Origin</p>
                  <p className="text-2xl font-bold mb-4">{origin}</p>
                  <div className="space-y-2 text-slate-300">
                    <p>Severity: <span className="font-bold">{explanation.weather.origin.weather_severity.toFixed(2)}</span></p>
                    <p>Condition: {explanation.weather.origin.weather_condition}</p>
                    <p>Wind: {explanation.weather.origin.wind_speed_ms} m/s</p>
                    <p>Temp: {explanation.weather.origin.temperature_c.toFixed(1)}°C</p>
                  </div>
                </div>

                <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                  <p className="text-slate-400 text-sm mb-2">Destination</p>
                  <p className="text-2xl font-bold mb-4">{destination}</p>
                  <div className="space-y-2 text-slate-300">
                    <p>Severity: <span className="font-bold">{explanation.weather.destination.weather_severity.toFixed(2)}</span></p>
                    <p>Condition: {explanation.weather.destination.weather_condition}</p>
                    <p>Wind: {explanation.weather.destination.wind_speed_ms} m/s</p>
                    <p>Temp: {explanation.weather.destination.temperature_c.toFixed(1)}°C</p>
                  </div>
                </div>
              </div>
            </div>

            {/* News Signals */}
            <div className="bg-slate-800 rounded-xl shadow-xl p-8 border border-slate-700">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Newspaper className="w-6 h-6 text-blue-400" />
                  <h3 className="text-xl font-semibold text-slate-200">
                    Current News Signals
                  </h3>
                </div>
                {explanation.news_signals && explanation.news_signals.length > 0 && (
                  <span className="text-sm text-slate-400">
                    Avg Risk: {explanation.news_risk_avg.toFixed(2)}
                  </span>
                )}
              </div>
              
              {!explanation.news_signals || explanation.news_signals.length === 0 ? (
                <div className="text-center py-12 text-slate-400 bg-slate-700/50 rounded-lg border border-slate-600">
                  <Newspaper className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p className="text-lg font-medium mb-2">No location-specific news available</p>
                  <p className="text-sm">
                    The system will use general supply chain trends for risk calculation.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {explanation.news_signals.map((news, idx) => (
                    <div key={idx} className="bg-slate-700 rounded-lg p-6 border border-slate-600 hover:border-slate-500 transition">
                      <p className="text-slate-300 mb-2 font-medium">{news.headline}</p>
                      <div className="flex items-center gap-4 text-sm text-slate-400">
                        <span>Category: {news.category}</span>
                        <span>•</span>
                        <span>Risk: {news.risk_score.toFixed(2)}</span>
                        <span>•</span>
                        <span>{news.time ? news.time.split('T')[0] : 'N/A'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Similar Events */}
            <div className="bg-slate-800 rounded-xl shadow-xl p-8 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <Search className="w-6 h-6 text-blue-400" />
                <h3 className="text-xl font-semibold text-slate-200">
                  Similar Historical Events
                </h3>
              </div>
              
              {!explanation.similar_events || explanation.similar_events.length === 0 ? (
                <div className="text-center py-12 text-slate-400 bg-slate-700/50 rounded-lg border border-slate-600">
                  <Search className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p className="text-lg font-medium mb-2">No similar historical events found</p>
                  <p className="text-sm">
                    This route may have limited historical disruption data.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {explanation.similar_events.map((event, idx) => (
                    <div key={idx} className="bg-slate-700 rounded-lg p-6 border border-slate-600 hover:border-slate-500 transition">
                      <div className="flex items-start justify-between mb-3">
                        <p className="text-slate-300 flex-1 font-medium">{event.headline}</p>
                        <span className="ml-4 px-3 py-1 bg-blue-900 text-blue-200 rounded-lg text-sm font-semibold whitespace-nowrap">
                          {Math.round(event.similarity * 100)}% match
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-slate-400">
                        <span>Risk: {event.risk_score.toFixed(2)}</span>
                        <span>•</span>
                        <span>{event.category}</span>
                        <span>•</span>
                        <span>{event.date ? event.date.split('T')[0] : 'N/A'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Forecast Chart */}
            <div className="bg-slate-800 rounded-xl shadow-xl p-8 border border-slate-700">
              <h3 className="text-xl font-semibold mb-6 flex items-center text-slate-200">
                <span className="text-2xl mr-3">📈</span>
                Delay Forecast
              </h3>
              
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={getForecastData()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis dataKey="horizon" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" label={{ value: 'Days Delay', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="delay" stroke="#3b82f6" strokeWidth={3} name="Expected Delay (days)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!explanation && !loading && (
          <div className="bg-slate-800 rounded-xl shadow-xl p-16 text-center border border-slate-700">
            <div className="text-6xl mb-6">🚢</div>
            <h3 className="text-2xl font-semibold mb-4 text-slate-200">
              Select a route to begin
            </h3>
            <p className="text-slate-400 max-w-md mx-auto">
              Choose an origin and destination port above, then click "Explain Risk" to generate a comprehensive risk assessment powered by 7 HuggingFace ML models.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-700 bg-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-slate-400 text-sm">
          <p>FreightSense © 2026 | Powered by 7 HuggingFace Tasks + Real-Time Data</p>
          <p className="text-xs mt-2 text-slate-500">
            RSS News • Live Weather API • ChromaDB Vector Search • Amazon Chronos Forecasting
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;