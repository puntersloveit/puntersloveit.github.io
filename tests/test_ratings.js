const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const context = {};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../assets/js/ratings.js"), "utf8"), context);
const conferences = (rows, year) => Array.from(context.getSeasonConferences(rows, year));
const rows = [
  {season: "2015", awayConference: "Retired", homeConference: "SEC"},
  {season: "2026", awayConference: "SEC", homeConference: "New"},
  {season: "2026", awayConference: " SEC ", homeConference: ""},
  {season: "2026", awayConference: null, homeConference: "   "},
].map(row => ({awayDivision: "fbs", homeDivision: "fbs", ...row}));
test("only conferences present in the selected season are offered", () => {
  assert.deepEqual(conferences(rows, 2026), ["New", "SEC"]);
  assert.deepEqual(conferences(rows, "2015"), ["Retired", "SEC"]);
});
test("all years offers the historical union without blanks or duplicates", () => {
  assert.deepEqual(conferences(rows, "-1"), ["New", "Retired", "SEC"]);
});
test("an empty season has no conference entries", () => {
  assert.deepEqual(conferences(rows, 2000), []);
});
test("FCS and unknown divisions are excluded, FBS opponents retained", () => {
  assert.deepEqual(conferences([
    {season: "2026", awayConference: "Big Sky", awayDivision: "fcs", homeConference: "SEC", homeDivision: "fbs"},
    {season: "2026", awayConference: "Unknown", homeConference: "FCS Independents", homeDivision: "fcs"},
  ], 2026), ["SEC"]);
});
test("precomputed index keeps season-specific membership and the historical union", () => {
  const index = context.buildConferenceIndex(rows);
  assert.deepEqual(Array.from(index.get("2015")), ["Retired", "SEC"]);
  assert.deepEqual(Array.from(index.get("2026")), ["New", "SEC"]);
  assert.deepEqual(Array.from(index.get("-1")), ["New", "Retired", "SEC"]);
});
const game = {season: "2026", week: "bowls", awayTeam: "Oregon", homeTeam: "Georgia",
  awayConference: "Big Ten", homeConference: "SEC"};
const any = {year: "-1", week: "all", team: "All", conference: "All"};
test("combined filters match either team and either conference", () => {
  assert.equal(context.matchesGameFilters(game, any), true);
  assert.equal(context.matchesGameFilters(game,
    {year: "2026", week: "bowls", team: "Oregon", conference: "SEC"}), true);
  assert.equal(context.matchesGameFilters(game, {...any, team: "Georgia", conference: "Big Ten"}), true);
  for (const filters of [{year: "2025"}, {week: "1"}, {team: "Alabama"}, {conference: "ACC"}]) {
    assert.equal(context.matchesGameFilters(game, {...any, ...filters}), false);
  }
});
test("NFL games continue filtering without conference metadata", () => {
  assert.equal(context.matchesGameFilters({season: "2025", week: "playoff",
    homeTeam: "BUF", awayTeam: "KC"}, {...any, year: "2025", week: "playoff", team: "KC"}), true);
});
