// -----------------------------
// IMPORTS
// -----------------------------

import { useState } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
} from "chart.js";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement);

// -----------------------------
// MAIN COMPONENT
// -----------------------------

function App() {
  const [query, setQuery] = useState("Iran US war");
  const [news, setNews] = useState([]);
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [trend, setTrend] = useState({});
  const [socialSummary, setSocialSummary] = useState("");
  const [tab, setTab] = useState("news");
  const [alert, setAlert] = useState("");
  const [riskExplanation, setRiskExplanation] = useState([]);

  // 🔥 NEW STATES (ADDED)
  const [riskScore, setRiskScore] = useState(0);
  const [riskLabel, setRiskLabel] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [imageResult, setImageResult] = useState("");
  const [imageLoading, setImageLoading] = useState(false);

  // -----------------------------
  // FETCH DATA
  // -----------------------------
  const API_URL = import.meta.env.VITE_API_URL;

  const fetchNews = async () => {
    setLoading(true);

    try {
      const res = await axios.get(
        `${API_URL}/news?query=${encodeURIComponent(query)}`,
      );

      setNews(res.data.articles);
      setSummary(res.data.summary);
      setTrend(res.data.trend);
      setSocialSummary(res.data.social_summary);
      setRiskScore(res.data.risk_score);
      setRiskLabel(res.data.risk_label);
      setAlert(res.data.alert);
      setRiskExplanation(res.data.risk_explanation);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 🔥 NEW FUNCTION (IMAGE ANALYSIS)
  const analyzeImage = async () => {
    if (!imageUrl) return;

    setImageLoading(true);
    setImageResult("");

    try {
      const res = await axios.get(
        `http://127.0.0.1:8000/analyze-image?image_url=${imageUrl}`,
      );

      setImageResult(res.data.analysis);
    } catch (err) {
      console.error(err);
      setImageResult("Error analyzing image");
    }

    setImageLoading(false);
  };

  // -----------------------------
  // HELPER → COLOR BY TYPE
  // -----------------------------

  const getTypeColor = (type) => {
    if (!type) return "gray";

    if (type.includes("Military")) return "red";
    if (type.includes("Strategic")) return "purple";
    return "gray";
  };

  // -----------------------------
  // UI
  // -----------------------------

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🌍 OSINT Monitoring Dashboard</h1>

      {/* SEARCH */}
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ padding: "10px", width: "300px" }}
      />

      <button onClick={fetchNews} style={{ marginLeft: "10px" }}>
        Search
      </button>

      {loading && <p>Loading...</p>}

      {/* AI SUMMARY */}
      {summary && (
        <div
          style={{ marginTop: "20px", background: "#f4f4f4", padding: "15px" }}
        >
          <h2>🧠 AI Intelligence Summary</h2>
          <p>{summary}</p>
        </div>
      )}

      {/* 🚨 RISK INDICATOR */}
      {riskLabel && (
        <div
          style={{
            marginTop: "20px",
            padding: "15px",
            background: riskLabel.includes("High")
              ? "#ff4d4d"
              : riskLabel.includes("Medium")
                ? "#ffa500"
                : "#4caf50",
            color: "white",
            borderRadius: "8px",
          }}
        >
          {/* 🧠 RISK EXPLANATION */}
          {riskExplanation.length > 0 && (
            <div
              style={{
                marginTop: "15px",
                padding: "12px",
                background: "#222",
                color: "white",
                borderRadius: "8px",
              }}
            >
              <h3>🧠 Why this risk level?</h3>

              <ul>
                {riskExplanation.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {/* 🚨 ALERT DISPLAY */}
          {alert && (
            <div
              style={{
                marginTop: "15px",
                padding: "12px",
                background: "#ff3333",
                color: "white",
                borderRadius: "8px",
                fontWeight: "bold",
              }}
            >
              {alert}
            </div>
          )}
          <h2>🚨 Threat Level</h2>
          <p style={{ fontSize: "18px" }}>
            {riskLabel} (Score: {riskScore}/100)
          </p>
        </div>
      )}

      {/* SOCIAL SUMMARY */}
      {socialSummary && (
        <div
          style={{
            marginTop: "20px",
            background: "#222",
            padding: "15px",
            color: "white",
          }}
        >
          <h2>💬 Social Media Insights</h2>
          <p>{socialSummary}</p>
        </div>
      )}

      {/* TABS */}
      <div style={{ marginTop: "20px" }}>
        <button onClick={() => setTab("news")}>📰 News</button>
        <button onClick={() => setTab("analytics")}>📊 Analytics</button>
        <button onClick={() => setTab("map")}>🗺️ Map</button>

        {/* 🔥 NEW TAB */}
        <button onClick={() => setTab("image")}>🖼️ Image</button>
      </div>

      {/* -----------------------------
          📰 NEWS TAB
      ----------------------------- */}

      {tab === "news" && (
        <div style={{ marginTop: "20px" }}>
          {news.map((item, index) => (
            <div
              key={index}
              style={{
                border: "1px solid #ddd",
                padding: "10px",
                marginBottom: "10px",
                background: item.source.includes("Social")
                  ? "#f0f8ff"
                  : "white",
              }}
            >
              <h3>{item.title}</h3>
              <p>{item.description}</p>

              <span
                style={{
                  padding: "3px 8px",
                  background: item.source.includes("BBC")
                    ? "green"
                    : item.source.includes("Reuters")
                      ? "blue"
                      : item.source.includes("Social")
                        ? "orange"
                        : "gray",
                  color: "white",
                  borderRadius: "5px",
                  fontSize: "12px",
                }}
              >
                {item.source}
              </span>

              {item.sentiment && (
                <span style={{ marginLeft: "10px", fontSize: "12px" }}>
                  Sentiment: {item.sentiment}
                </span>
              )}

              {item.type && (
                <span
                  style={{
                    marginLeft: "10px",
                    padding: "3px 8px",
                    background: getTypeColor(item.type),
                    color: "white",
                    borderRadius: "5px",
                    fontSize: "12px",
                  }}
                >
                  {item.type}
                </span>
              )}
              {/* 📊 CREDIBILITY */}
              {item.credibility && (
                <span
                  style={{
                    marginLeft: "10px",
                    padding: "3px 8px",
                    background:
                      item.credibility === "High"
                        ? "green"
                        : item.credibility === "Medium"
                          ? "orange"
                          : "red",
                    color: "white",
                    borderRadius: "5px",
                    fontSize: "12px",
                  }}
                >
                  {item.credibility} Source
                </span>
              )}
              {/* 🚨 MISINFORMATION WARNING */}
              {item.misinformation && (
                <p style={{ color: "red", fontSize: "13px", marginTop: "5px" }}>
                  {item.misinformation}
                </p>
              )}

              {item.importance && (
                <p
                  style={{ marginTop: "8px", fontSize: "13px", color: "#444" }}
                >
                  ⚠️ {item.importance}
                </p>
              )}

              <br />
              <a href={item.url} target="_blank">
                Read more
              </a>
            </div>
          ))}
        </div>
      )}

      {/* -----------------------------
          📊 ANALYTICS TAB
      ----------------------------- */}

      {tab === "analytics" && (
        <div style={{ marginTop: "20px", background: "#111", padding: "15px" }}>
          <h2 style={{ color: "white" }}>📊 Trend Analysis</h2>

          <Line
            data={{
              labels: Object.keys(trend),
              datasets: [
                {
                  label: "News Volume",
                  data: Object.values(trend),
                  borderColor: "cyan",
                },
              ],
            }}
          />
        </div>
      )}

      {/* -----------------------------
          🗺️ MAP TAB
      ----------------------------- */}

      {tab === "map" && (
        <MapContainer center={[20, 0]} zoom={2} style={{ height: "400px" }}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />

          {news.map((item, i) =>
            item.locations?.map((loc, j) => {
              if (!loc.lat || !loc.lon) return null;

              return (
                <Marker key={`${i}-${j}`} position={[loc.lat, loc.lon]}>
                  <Popup>
                    <b>{item.title}</b>
                    <br />
                    📍 {loc.name}
                  </Popup>
                </Marker>
              );
            }),
          )}
        </MapContainer>
      )}

      {/* -----------------------------
          🖼️ IMAGE TAB (NEW)
      ----------------------------- */}

      {tab === "image" && (
        <div style={{ marginTop: "20px" }}>
          <h2>🖼️ Image Intelligence</h2>

          <input
            type="text"
            placeholder="Paste Image URL"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            style={{ padding: "10px", width: "400px" }}
          />

          <button onClick={analyzeImage} style={{ marginLeft: "10px" }}>
            Analyze
          </button>

          {imageLoading && <p>Analyzing...</p>}

          {imageResult && (
            <div
              style={{
                marginTop: "20px",
                background: "#f4f4f4",
                padding: "15px",
              }}
            >
              <h3>🧠 Result</h3>
              <p>{imageResult}</p>
            </div>
          )}

          {imageUrl && (
            <img
              src={imageUrl}
              alt="preview"
              style={{ marginTop: "20px", maxWidth: "400px" }}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default App;
