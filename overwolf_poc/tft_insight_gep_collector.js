const fs = require("fs");
const path = require("path");

// Documented TFT features only. Augments intentionally excluded.
const FEATURES = [
  "game_info",
  "me",
  "match_info",
  "store",
  "board",
  "bench",
  "match_stats"
];

function timestamp() {
  return new Date().toISOString();
}

function createTftInsightCollector(app) {
  const outDir = path.join(process.cwd(), "data", "tft-insight-gep");
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(
    outDir,
    `gep_${timestamp().replace(/[:.]/g, "-")}.jsonl`
  );

  function write(kind, gameId, args) {
    fs.appendFileSync(
      outFile,
      JSON.stringify({
        captured_at: timestamp(),
        kind,
        game_id: gameId,
        args
      }) + "\n",
      "utf8"
    );
  }

  const gep = app.overwolf.packages.gep;

  gep.on("game-detected", async (event, gameId, ...args) => {
    write("game-detected", gameId, args);
    try {
      if (event && typeof event.enable === "function") event.enable();
      await gep.setRequiredFeatures(FEATURES);
      write("features-enabled", gameId, FEATURES);
    } catch (err) {
      write("error", gameId, [String(err)]);
    }
  });

  gep.on("new-info-update", (event, gameId, ...args) => {
    write("new-info-update", gameId, args);
  });

  gep.on("new-game-event", (event, gameId, ...args) => {
    write("new-game-event", gameId, args);
  });

  gep.on("game-exit", (event, gameId, ...args) => {
    write("game-exit", gameId, args);
  });

  gep.on("error", (...args) => {
    write("gep-error", null, args);
  });

  console.log("[TFT Insight] collector ready:", outFile);
  console.log("[TFT Insight] features:", FEATURES.join(", "));
  return outFile;
}

module.exports = { createTftInsightCollector, FEATURES };
