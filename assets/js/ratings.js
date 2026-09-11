function initializeDropdowns(config) {
  const seasonDropdown = document.getElementById("season");
  const weekDropdown = document.getElementById("week");
  const teamDropdown = document.getElementById("team");
  const messageElement = document.getElementById("no-records-message");
  const table = document.getElementById(config.tableId);
  const bodyRows = table.querySelectorAll("tbody tr");
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
    filterRecords();
  }

  function filterRecords() {
    const selectedYear = seasonDropdown.value;
    const selectedWeek = weekDropdown.value;
    const selectedTeam = teamDropdown.value.trim();
    let noRecordsFound = true;

    const isBowlsWeek = selectedWeek.toLowerCase() === "bowls";
    const showYearColumn = selectedYear === "-1";
    const showWeekColumn = selectedWeek === "All" && !isBowlsWeek;
    const showBowlsColumn = config.showBowlsColumn && isBowlsWeek;

    toggleColumnDisplay(0, showYearColumn); // 'Year' column
    toggleColumnDisplay(1, showWeekColumn); // 'Week' column
    if (config.showBowlsColumn) {
      toggleColumnDisplay(2, showBowlsColumn); // 'Bowls' column
    }

    for (const row of bodyRows) {
      const cells = row.children;
      const year = cells[0].textContent.trim();
      const week = cells[1].textContent.trim().toLowerCase();
      const teamStartIndex = config.showBowlsColumn ? 3 : 2;
      const awayTeam = cells[teamStartIndex].textContent.trim().replace(/\(\d+\)/g, "");
      const homeTeam = cells[teamStartIndex + 1].textContent.trim().replace(/\(\d+\)/g, "");

      const matchesTeam = selectedTeam === "All" || awayTeam === selectedTeam || homeTeam === selectedTeam;
      const matchesWeek = selectedWeek === "All" || week === selectedWeek.toLowerCase();
      const matchesYear = selectedYear === "-1" || year === selectedYear;

      const shouldDisplayRow = matchesTeam && matchesWeek && matchesYear;

      row.style.display = shouldDisplayRow ? "" : "none";
      if (shouldDisplayRow) {
        noRecordsFound = false;
      }
    }

    if (noRecordsFound) {
      messageElement.textContent = translate("no_records_games", {
        team: selectedTeam === "All" ? translate("all_teams") : selectedTeam,
        week: optionLabel(selectedWeek),
        year: selectedYear === "-1" ? translate("all_years") : selectedYear
      });
      messageElement.style.display = "block";
    } else {
      messageElement.style.display = "none";
    }
  }

  function toggleColumnDisplay(columnIndex, showColumn) {
    const displayStyle = showColumn ? "" : "none";
    const headerCells = document.querySelectorAll(`#${config.tableId} thead th`);
    if (headerCells.length > 0) {
      headerCells[columnIndex].style.display = displayStyle;
    }
    for (const row of bodyRows) {
      const cell = row.children[columnIndex];
      if (cell) {
        cell.style.display = displayStyle;
      }
    }
  }

  // Initialize page
  populateSeasonDropdown();
  populateTeamDropdown();
  updateWeeks();
  filterRecords();
  table.style.display = "";

  // Add event listeners
  seasonDropdown.addEventListener("change", updateWeeks);
  weekDropdown.addEventListener("change", filterRecords);
  teamDropdown.addEventListener("change", filterRecords);

  document.addEventListener("puntersloveit:languagechange", function () {
    Array.from(seasonDropdown.options).forEach(option => {
      if (option.value === "-1") option.textContent = translate("all_years");
    });
    Array.from(teamDropdown.options).forEach(option => {
      if (option.value === "All") option.textContent = translate("all_teams");
    });
    Array.from(weekDropdown.options).forEach(option => option.textContent = optionLabel(option.value));
    filterRecords();
  });
}
