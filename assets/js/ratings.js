function buildConferenceIndex(rows) {
  const seasons = new Map([["-1", new Set()]]);
  rows.forEach(row => {
    const year = String(row.season);
    if (!seasons.has(year)) seasons.set(year, new Set());
    [[row.awayConference, row.awayDivision], [row.homeConference, row.homeDivision]].forEach(([name, division]) => {
      if (division === "fbs" && name && name.trim()) {
        seasons.get(year).add(name.trim());
        seasons.get("-1").add(name.trim());
      }
    });
  });
  return new Map(Array.from(seasons, ([year, names]) =>
    [year, Array.from(names).sort((a, b) => a.localeCompare(b))]));
}

function getSeasonConferences(rows, season) {
  return buildConferenceIndex(rows).get(String(season)) || [];
}

function matchesGameFilters(game, filters) {
  return (filters.year === "-1" || game.season === filters.year)
    && (filters.week === "all" || game.week === filters.week)
    && (filters.team === "All" || game.awayTeam === filters.team || game.homeTeam === filters.team)
    && (filters.conference === "All" || game.awayConference === filters.conference
      || game.homeConference === filters.conference);
}

function initializeDropdowns(config) {
  const seasonDropdown = document.getElementById("season");
  const weekDropdown = document.getElementById("week");
  const teamDropdown = document.getElementById("team");
  const conferenceDropdown = document.getElementById("conference");
  const messageElement = document.getElementById("no-records-message");
  const table = document.getElementById(config.tableId);
  // Read immutable metadata once, never from DOM cells during filtering.
  const teamStartIndex = config.showBowlsColumn ? 3 : 2;
  const games = Array.from(table.querySelectorAll("tbody tr"), row => ({
    element: row,
    season: row.children[0].textContent.trim(),
    week: row.children[1].textContent.trim().toLowerCase(),
    awayTeam: row.children[teamStartIndex].textContent.trim().replace(/\(\d+\)/g, "").trim(),
    homeTeam: row.children[teamStartIndex + 1].textContent.trim().replace(/\(\d+\)/g, "").trim(),
    awayConference: (row.dataset.awayConference || "").trim(),
    homeConference: (row.dataset.homeConference || "").trim(),
    awayDivision: row.dataset.awayDivision,
    homeDivision: row.dataset.homeDivision
  }));
  const gamesBySeason = new Map([["-1", games]]);
  games.forEach(game => {
    if (!gamesBySeason.has(game.season)) gamesBySeason.set(game.season, []);
    gamesBySeason.get(game.season).push(game);
  });
  const conferencesBySeason = conferenceDropdown ? buildConferenceIndex(games) : new Map();
  let visibleGames = new Set(games);
  const translate = (key, values) => window.PLI18n ? window.PLI18n.t(key, values) : key;

  function optionLabel(value) {
    const labels = {All: "all", Bowls: "bowls", Playoff: "playoff"};
    return labels[value] ? translate(labels[value]) : value;
  }

  function populateSeasonDropdown() {
    config.seasons.forEach(season => {
      const option = document.createElement("option");
      option.value = season.season;
      option.textContent = season.season == -1 ? translate("all_years") : season.season;
      seasonDropdown.appendChild(option);
    });
  }

  function populateTeamDropdown() {
    const allOption = document.createElement("option");
    allOption.value = "All";
    allOption.textContent = translate("all_teams");
    teamDropdown.appendChild(allOption);

    config.teams.teams.forEach(team => {
      const option = document.createElement("option");
      option.value = team;
      option.textContent = team;
      teamDropdown.appendChild(option);
    });
  }

  function updateConferences() {
    if (!conferenceDropdown) return;
    const previous = conferenceDropdown.value;
    const names = conferencesBySeason.get(seasonDropdown.value) || [];
    conferenceDropdown.replaceChildren();
    const all = document.createElement("option");
    all.value = "All";
    all.textContent = translate("all_conferences");
    conferenceDropdown.appendChild(all);
    names.forEach(name => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      conferenceDropdown.appendChild(option);
    });
    conferenceDropdown.value = names.includes(previous) ? previous : "All";
  }

  function updateWeeks() {
    const selectedSeason = seasonDropdown.value;
    weekDropdown.innerHTML = "";
    const selectedData = config.seasons.find(item => item.season == selectedSeason);

    if (selectedData) {
      selectedData.weeks.forEach(week => {
        const option = document.createElement("option");
        option.value = week;
        option.textContent = optionLabel(week);
        weekDropdown.appendChild(option);
      });
    }
    updateConferences();
    filterRecords();
  }

  function filterRecords() {
    const selectedYear = seasonDropdown.value;
    const selectedWeek = weekDropdown.value;
    const selectedTeam = teamDropdown.value.trim();
    const selectedConference = conferenceDropdown ? conferenceDropdown.value : "All";

    const isBowlsWeek = selectedWeek.toLowerCase() === "bowls";
    const showYearColumn = selectedYear === "-1";
    const showWeekColumn = selectedWeek === "All" && !isBowlsWeek;
    const showBowlsColumn = config.showBowlsColumn && isBowlsWeek;

    toggleColumnDisplay("ratings-hide-year", showYearColumn);
    toggleColumnDisplay("ratings-hide-week", showWeekColumn);
    if (config.showBowlsColumn) {
      toggleColumnDisplay("ratings-hide-bowls", showBowlsColumn);
    }

    const filters = {year: selectedYear, week: selectedWeek.toLowerCase(),
      team: selectedTeam, conference: selectedConference};
    const candidates = gamesBySeason.get(selectedYear) || [];
    const nextVisible = new Set(candidates.filter(game => matchesGameFilters(game, filters)));
    // Only touch rows whose visibility changed, including on season switches.
    visibleGames.forEach(game => {
      if (!nextVisible.has(game)) game.element.style.display = "none";
    });
    nextVisible.forEach(game => {
      if (!visibleGames.has(game)) game.element.style.display = "";
    });
    visibleGames = nextVisible;

    if (visibleGames.size === 0) {
      messageElement.textContent = translate(conferenceDropdown ? "no_records_games_conference" : "no_records_games", {
        team: selectedTeam === "All" ? translate("all_teams") : selectedTeam,
        week: optionLabel(selectedWeek),
        year: selectedYear === "-1" ? translate("all_years") : selectedYear,
        conference: selectedConference === "All" ? translate("all_conferences") : selectedConference
      });
      messageElement.style.display = "block";
    } else {
      messageElement.style.display = "none";
    }
  }

  function toggleColumnDisplay(className, showColumn) {
    const hideColumn = !showColumn;
    if (table.classList.contains(className) !== hideColumn) {
      table.classList.toggle(className, hideColumn);
    }
  }

  // Initialize page
  populateSeasonDropdown();
  populateTeamDropdown();
  updateWeeks();
  table.style.display = "";

  // Add event listeners
  seasonDropdown.addEventListener("change", updateWeeks);
  weekDropdown.addEventListener("change", filterRecords);
  teamDropdown.addEventListener("change", filterRecords);
  if (conferenceDropdown) conferenceDropdown.addEventListener("change", filterRecords);

  document.addEventListener("puntersloveit:languagechange", function () {
    Array.from(seasonDropdown.options).forEach(option => {
      if (option.value === "-1") option.textContent = translate("all_years");
    });
    Array.from(teamDropdown.options).forEach(option => {
      if (option.value === "All") option.textContent = translate("all_teams");
    });
    Array.from(weekDropdown.options).forEach(option => option.textContent = optionLabel(option.value));
    updateConferences();
    filterRecords();
  });
}
