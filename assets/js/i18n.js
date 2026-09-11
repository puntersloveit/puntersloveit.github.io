(function () {
  const translations = {
    en: {
      tagline: "spoiler-free ncaaf & nfl game ratings",
      site_description: "Spoiler-free NFL and college football game ratings that help you find the most entertaining games without revealing the result.",
      nav_nfl: "NFL",
      nav_ncaa: "NCAAF",
      nav_about: "About",
      nfl_game_ratings: "NFL Game Ratings",
      ncaa_game_ratings: "NCAAF Game Ratings",
      nfl_description: "Spoiler-free NFL game ratings ranked by excitement and watchability. Find the best NFL games to watch without seeing scores or results.",
      ncaa_description: "Spoiler-free NCAA college football game ratings ranked by excitement and watchability. Find the best NCAAF games without seeing results.",
      extended_ratings: "Extended ratings",
      team_ratings: "Most entertaining teams",
      game_ratings: "Game ratings",
      select_year: "Select Year:",
      select_week: "Select Week:",
      select_team: "Select Team:",
      conference: "Conference:",
      all_years: "All Years",
      all_teams: "All Teams",
      all_conferences: "All Conferences",
      all: "All",
      bowls: "Bowls",
      playoff: "Playoff",
      year: "Year",
      week: "Week",
      season_type: "Season Type",
      notes: "Notes",
      bowl_name: "Bowl Name",
      team: "Team",
      away_team: "Away Team",
      home_team: "Home Team",
      home_conference: "Home Conference",
      away_conference: "Away Conference",
      home_division: "Home Division",
      away_division: "Away Division",
      game_rating: "Game Rating",
      entertainment_rating: "Entertainment Rating",
      tds_rating: "TDs Rating",
      sacks_rating: "Sacks Rating",
      interceptions_rating: "Interceptions Rating",
      yards_rating: "Yards Rating",
      stat_rating: "Stat Rating",
      efficiency_rating: "Efficiency Rating",
      overtimes_rating: "Overtimes Rating",
      excitement_rating: "Excitement Rating",
      score_diff_rating: "Score Diff Rating",
      win_prob_shifts_rating: "Win Probability Shifts Rating",
      win_chances_max_diff_rating: "Maximum Win Chances Difference Rating",
      leader_changes_rating: "Leader Changes Rating",
      nfl_teams_title: "NFL Most Entertaining Teams",
      ncaa_teams_title: "NCAA FBS Most Entertaining Teams",
      extended_nfl_title: "Extended NFL Game Ratings",
      extended_ncaa_title: "Extended NCAA Game Ratings",
      unable_extended: "Unable to load extended ratings data.",
      no_records_year: "No records found for {year}.",
      no_records_conference: "No records found for {year} in {conference}.",
      no_records_games: "No records found for {team} in {week}, {year}.",
      language: "Language"
    },
    ru: {
      tagline: "рейтинги матчей NCAA и NFL без спойлеров",
      site_description: "Рейтинги матчей NFL и студенческого футбола без спойлеров: выбирайте самые интересные игры, не узнавая результат.",
      nav_nfl: "NFL",
      nav_ncaa: "NCAA",
      nav_about: "О сайте",
      nfl_game_ratings: "Рейтинг матчей NFL",
      ncaa_game_ratings: "Рейтинг матчей NCAA",
      nfl_description: "Рейтинг матчей NFL по зрелищности и интересности без счёта, результата и других спойлеров.",
      ncaa_description: "Рейтинг матчей студенческого футбола NCAA по зрелищности и интересности без результатов и спойлеров.",
      extended_ratings: "Подробный рейтинг",
      team_ratings: "Самые зрелищные команды",
      game_ratings: "Рейтинг матчей",
      select_year: "Выберите сезон:",
      select_week: "Выберите неделю:",
      select_team: "Выберите команду:",
      conference: "Конференция:",
      all_years: "Все сезоны",
      all_teams: "Все команды",
      all_conferences: "Все конференции",
      all: "Все",
      bowls: "Боулы",
      playoff: "Плей-офф",
      year: "Сезон",
      week: "Неделя",
      season_type: "Этап сезона",
      notes: "Примечания",
      bowl_name: "Название боула",
      team: "Команда",
      away_team: "Гости",
      home_team: "Хозяева",
      home_conference: "Конференция хозяев",
      away_conference: "Конференция гостей",
      home_division: "Дивизион хозяев",
      away_division: "Дивизион гостей",
      game_rating: "Рейтинг матча",
      entertainment_rating: "Рейтинг зрелищности",
      tds_rating: "Рейтинг тачдаунов",
      sacks_rating: "Рейтинг сэков",
      interceptions_rating: "Рейтинг перехватов",
      yards_rating: "Рейтинг ярдов",
      stat_rating: "Статистический рейтинг",
      efficiency_rating: "Рейтинг результативности",
      overtimes_rating: "Рейтинг овертаймов",
      excitement_rating: "Рейтинг напряжённости",
      score_diff_rating: "Рейтинг разницы в счёте",
      win_prob_shifts_rating: "Рейтинг колебаний вероятности победы",
      win_chances_max_diff_rating: "Рейтинг размаха шансов на победу",
      leader_changes_rating: "Рейтинг смен лидера",
      nfl_teams_title: "Самые зрелищные команды NFL",
      ncaa_teams_title: "Самые зрелищные команды NCAA FBS",
      extended_nfl_title: "Подробный рейтинг матчей NFL",
      extended_ncaa_title: "Подробный рейтинг матчей NCAA",
      unable_extended: "Не удалось загрузить подробные рейтинги.",
      no_records_year: "Для сезона {year} ничего не найдено.",
      no_records_conference: "Для {conference}, сезон {year}, ничего не найдено.",
      no_records_games: "Для команды {team}, неделя {week}, сезон {year}, ничего не найдено.",
      language: "Язык"
    }
  };

  function interpolate(text, values) {
    return Object.keys(values || {}).reduce((result, key) => result.replaceAll(`{${key}}`, values[key]), text);
  }

  function getLanguage() {
    return document.documentElement.lang === "ru" ? "ru" : "en";
  }

  function t(key, values) {
    const language = getLanguage();
    return interpolate(translations[language][key] || translations.en[key] || key, values);
  }

  function translatePage() {
    document.querySelectorAll("[data-i18n]").forEach(element => {
      element.textContent = t(element.dataset.i18n);
    });
    document.querySelectorAll("[data-lang-content]").forEach(element => {
      element.hidden = element.dataset.langContent !== getLanguage();
    });
    document.querySelectorAll("[data-language-choice]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.languageChoice === getLanguage()));
    });
  }

  function setLanguage(language, persist) {
    const selected = language === "ru" ? "ru" : "en";
    document.documentElement.lang = selected;
    if (persist) {
      try { localStorage.setItem("puntersloveit-language", selected); } catch (error) { /* Storage may be disabled. */ }
    }
    translatePage();
    document.dispatchEvent(new CustomEvent("puntersloveit:languagechange", {detail: {language: selected}}));
  }

  window.PLI18n = {getLanguage, setLanguage, t, translatePage};
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-language-choice]").forEach(button => {
      button.addEventListener("click", () => setLanguage(button.dataset.languageChoice, true));
    });
    translatePage();
  });
})();
