//
//  ContentView.swift
//  Test
//
//  Created by Maxim Akishin on 31.12.24.
//
import SwiftUI



#Preview {
    MainView()
}



struct MainView: View {
    // MARK: - Properties
    @State private var searchText: String = ""
    @State private var suggestions: [String] = []
    @State private var selectedTeams: Set<String> = []
    @State private var isSearchActive: Bool = false
    @State private var popularTeams: [String] = []
    @State private var popularNations: [String] = []
    @State private var popularTournaments: [String] = []
    @State private var navigateToResults = false
    @FocusState private var isSearchFocused: Bool
    
    var body: some View {
        NavigationView {
            GeometryReader { geometry in
                ZStack(alignment: .top) {
                    // Background colors
                    VStack(spacing: 0) {
                        Color(red: 0.024, green: 0.216, blue: 0.451)
                            .frame(height: UIScreen.main.bounds.height * 13 / 100)
                            .overlay(
                                // Logo and title directly on blue background
                                ZStack {
                                    HStack {
                                        Image("Check24")
                                            .resizable()
                                            .scaledToFit()
                                            .frame(width: 80, height: 80)
                                            .padding(.leading)
                                            .padding(.top, 40)
                                        Spacer()
                                    }
                                    Text("Favoritenauswahl")
                                        .foregroundColor(.white)
                                        .font(.system(size: 20, weight: .bold))
                                        .padding(.top, 40)
                                }
                            )
                        Color.white
                    }
                    .edgesIgnoringSafeArea(.all)
                    
                    // Main content
                    VStack(spacing: 20) {
                        // Spacer for blue header area
                        Color.clear
                            .frame(height: UIScreen.main.bounds.height * 5 / 100)
                        
                        // Search bar
                        searchBarView
                            .zIndex(1)
                        
                        // Scrollable content
                        ScrollView {
                            VStack(spacing: 20) {
                                if isSearchActive {
                                    searchResultsView
                                } else {
                                    popularItemsView
                                }
                            }
                            .padding(.bottom, 50) // Increased for button + white space
                        }
                    }
                    
                    // Fixed compare button at bottom with white background
                    VStack(spacing: 0) {
                        Spacer()
                        compareButton
                            .padding(.bottom, 10)
                            .padding(.top, 20)
                            .background(
                                Color.white
                                    .edgesIgnoringSafeArea(.bottom)
                            )
                    }
                }
                .frame(width: geometry.size.width, height: geometry.size.height)
                .onTapGesture {
                    isSearchFocused = false
                }
            }
            .navigationBarHidden(true)
            .ignoresSafeArea(.keyboard)
        }
        .onAppear {
            loadPopularTeams()
        }
        .preferredColorScheme(.light)
    }
    
    // MARK: - Subviews
    
    // Search bar
    private var searchBarView: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.gray)
                .padding(.leading, 20)
            
            TextField("Verein oder Wettbewerb suchen", text: $searchText)
                .focused($isSearchFocused)
                .font(.system(size: 17))
                .onChange(of: searchText) { text in
                    isSearchActive = !text.isEmpty
                    if text.count >= 2 {
                        searchTeams(query: text)
                    } else {
                        suggestions = []
                    }
                }
            
            if !searchText.isEmpty {
                Button(action: {
                    searchText = ""
                    suggestions = []
                    isSearchActive = false
                    isSearchFocused = false
                }) {
                    Image(systemName: "xmark")
                        .foregroundColor(.gray)
                        .padding(.trailing, 20)
                }
            }
        }
        .frame(height: 50)
        .background(Color(.systemGray6))
        .cornerRadius(25)
        .padding(.horizontal, 20)
    }
    
    // Search results
    private var searchResultsView: some View {
        ScrollView {
            VStack(alignment: .leading) {
                if !selectedTeams.isEmpty {
                    selectedTeamsSection
                }
                if !suggestions.isEmpty {
                    suggestionsSection
                }
            }
        }
    }
    
    // Selected teams section
    private var selectedTeamsSection: some View {
        VStack(alignment: .leading) {
            Text("Vereine")
                .font(.headline)
                .padding(.horizontal, 20)
            
            ForEach(Array(selectedTeams), id: \.self) { team in
                TeamButton(
                    team: team,
                    isSelected: true,
                    action: { selectedTeams.remove(team) }
                )
                .padding(.horizontal, 20)
            }
        }
    }
    
    // Suggestions section
    private var suggestionsSection: some View {
        VStack(alignment: .leading) {
            ForEach(suggestions.filter { !selectedTeams.contains($0) }, id: \.self) { team in
                TeamButton(
                    team: team,
                    isSelected: false,
                    action: { selectedTeams.insert(team) }
                )
                .padding(.horizontal, 20)
            }
        }
    }
    
    // Popular items view
    private var popularItemsView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                popularTeamsSection
                popularTournamentsSection
                popularNationsSection
            }
            .padding(.bottom, 50)
            .padding(.horizontal, 20)
        }
    }
    
    // Compare button with navigation
    private var compareButton: some View {
        Button(action: {
            navigateToResults = true
        }) {
            Text("Pakete vergleichen")
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .frame(height: 50)
                .background(Color.blue)
                .cornerRadius(25)
                .padding(.horizontal, 20)
        }
        .padding(.bottom, 0)
        .background(
            NavigationLink(
                destination: ResultView(selectedTeams: Array(selectedTeams)),
                isActive: $navigateToResults,
                label: { EmptyView() }
            )
        )
    }
    
    // MARK: - API Calls
    
    // Load popular teams from API
    private func loadPopularTeams() {
     //   guard let url = URL(string: "http://localhost:8000/api/v1/suggestions/") else { return }
        guard let url = URL(string: "https://check24.zapto.org/api/v1/suggestions/") else { return }
        
        URLSession.shared.dataTask(with: url) { data, _, error in
            if let data = data,
               let response = try? JSONDecoder().decode(SuggestionsResponse.self, from: data) {
                DispatchQueue.main.async {
                    self.popularTeams = response.popular_teams
                    self.popularNations = response.nations
                    self.popularTournaments = response.tournaments
                }
            }
        }.resume()
    }
    
    // Search teams
    private func searchTeams(query: String) {
        guard let url = URL(string: "https://check24.zapto.org/api/v1/search?query=\(query)") else { return }
        
        URLSession.shared.dataTask(with: url) { data, _, error in
            if let data = data,
               let response = try? JSONDecoder().decode(SearchResponse.self, from: data) {
                DispatchQueue.main.async {
                    self.suggestions = response.suggestions
                }
            }
        }.resume()
    }
    
    // MARK: - Popular Sections
    private var popularTeamsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Beliebte Vereine")
                .font(.headline)
            
            LazyVGrid(
                columns: [
                    GridItem(.adaptive(minimum: 150, maximum: 200), spacing: 8)
                ],
                spacing: 8
            ) {
                ForEach(popularTeams, id: \.self) { team in
                    PopularTeamButton(
                        team: team,
                        isSelected: selectedTeams.contains(team),
                        action: {
                            if selectedTeams.contains(team) {
                                selectedTeams.remove(team)
                            } else {
                                selectedTeams.insert(team)
                            }
                        }
                    )
                }
            }
        }
    }
    
    private var popularTournamentsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Beliebte Turniere")
                .font(.headline)
            
            LazyVGrid(
                columns: [
                    GridItem(.adaptive(minimum: 150, maximum: 200), spacing: 8)
                ],
                spacing: 8
            ) {
                ForEach(popularTournaments, id: \.self) { tournament in
                    PopularTeamButton(
                        team: tournament,
                        isSelected: selectedTeams.contains(tournament),
                        action: {
                            if selectedTeams.contains(tournament) {
                                selectedTeams.remove(tournament)
                            } else {
                                selectedTeams.insert(tournament)
                            }
                        }
                    )
                }
            }
        }
    }
    
    private var popularNationsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Beliebte Nationen")
                .font(.headline)
            
            LazyVGrid(
                columns: [
                    GridItem(.adaptive(minimum: 150, maximum: 200), spacing: 8)
                ],
                spacing: 8
            ) {
                ForEach(popularNations, id: \.self) { nation in
                    PopularTeamButton(
                        team: nation,
                        isSelected: selectedTeams.contains(nation),
                        action: {
                            if selectedTeams.contains(nation) {
                                selectedTeams.remove(nation)
                            } else {
                                selectedTeams.insert(nation)
                            }
                        }
                    )
                }
            }
        }
    }
}


struct SuggestionsResponse: Codable {
    let status: String
    let popular_teams: [String]
    let nations: [String]
    let tournaments: [String]
}

struct SearchResponse: Codable {
    let suggestions: [String]
}

struct TeamButton: View {
    let team: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                Circle()
                    .fill(Color.gray.opacity(0.2))
                    .frame(width: 30, height: 30)
                
                Text(team)
                    .foregroundColor(.black)
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(isSelected ? Color.blue.opacity(0.1) : Color.white)
            .cornerRadius(25)
            .overlay(
                RoundedRectangle(cornerRadius: 25)
                    .stroke(Color.gray.opacity(0.3), lineWidth: 1)
            )
        }
    }
}

// MARK: - Team Button Views
struct PopularTeamButton: View {
    let team: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: "tshirt")
                    .foregroundColor(.gray)
                    .frame(width: 24, height: 24)
                
                Text(team)
                    .foregroundColor(.black)
                    .font(.system(size: 14))
            }
            .padding(.vertical, 12)
            .padding(.horizontal, 16)
            .background(isSelected ? Color.blue.opacity(0.1) : Color.white)
            .cornerRadius(25)
            .overlay(
                RoundedRectangle(cornerRadius: 25)
                    .stroke(isSelected ? Color.blue : Color.gray.opacity(0.3), lineWidth: 1)
            )
        }
    }
}

// MARK: - Data Models
// Basic response structure from the API
struct APIResponse: Codable {
    let meta: Meta
    let data: APIData
    let status: String
}

// Meta information about the request
struct Meta: Codable {
    let mainLeague: String
    let teamsRequested: [String]
}

// Main data structure containing packages and statistics
struct APIData: Codable {
    let selected_packages: [Package]
    let total_cost: Double
    let coverage_ratio: String
    let weighted_coverage: String
    let unstreamable_games: [Game]
}

// Structure for a streaming package
struct Package: Codable {
    let name: String
    let costInEuro: Double
    let gamesCovered: [Game]
    let subscriptionType: String    // "monthly" or "yearly"
    let activeMonths: [String]      // Which months this package is active
}

// Structure for a single game
struct Game: Codable {
    let homeTeam: String
    let awayTeam: String
    let tournament: String
    let date: String
}

// MARK: - Main Result View
struct ResultView: View {
    // Properties
    let selectedTeams: [String]
    @State private var resultData: APIResponse? = nil
    @State private var isLoading = true
    @State private var errorMessage: String? = nil
    @State private var startDate = Date()
    
    var body: some View {
        VStack {
            // Date picker to select start date
            DatePicker(
                "Startdatum",
                selection: $startDate,
                displayedComponents: [.date]
            )
            .padding()
            .onChange(of: startDate) { _ in
                fetchData()
            }
            
            // Content based on loading state
            if isLoading {
                ProgressView("Laden...")
            } else if let error = errorMessage {
                Text("Fehler: \(error)")
                    .foregroundColor(.red)
            } else if let data = resultData {
                if data.data.selected_packages.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "exclamationmark.circle")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("Keine Spiele gefunden")
                            .font(.headline)
                        Text("Für den ausgewählten Zeitraum und die gewählten Teams sind keine Spiele verfügbar.")
                            .multilineTextAlignment(.center)
                            .foregroundColor(.gray)
                    }
                    .padding()
                } else {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 16) {
                            // Summary at the top
                            SummaryView(data: data.data)
                            
                            // Selected teams
                            Text("Ausgewählte Teams: \(data.meta.teamsRequested.joined(separator: ", "))")
                                .font(.subheadline)
                                .padding(.horizontal)
                            
                            // List of packages
                            ForEach(data.data.selected_packages, id: \.name) { package in
                                PackageView(package: package)
                            }
                            
                            // Unstreamable games at the bottom
                            UnstreamableGamesView(games: data.data.unstreamable_games)
                        }
                        .padding(.vertical)
                    }
                }
            }
        }
        .navigationTitle("Ergebnisse")
        .onAppear(perform: fetchData)
    }
    
    // MARK: - Data Fetching
    private func fetchData() {
        // Create URL with query parameters
        var components = URLComponents(string: "https://check24.zapto.org/api/v1/streaming-combinations/")!
        
        // Add selected teams and start date to query
        var queryItems = selectedTeams.map { URLQueryItem(name: "teams", value: $0) }
        let formatter = ISO8601DateFormatter()
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        queryItems.append(URLQueryItem(name: "start_date", value: formatter.string(from: startDate)))
        
        components.queryItems = queryItems
        
        guard let url = components.url else {
            errorMessage = "Ungültige URL: Die URL konnte nicht erstellt werden"
            isLoading = false
            return
        }
        
        // Make API request
        URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                isLoading = false
                
                if let error = error {
                    errorMessage = "Netzwerkfehler: \(error.localizedDescription)"
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    errorMessage = "Ungültige Server-Antwort: Keine HTTP-Antwort erhalten"
                    return
                }
                
                guard (200...299).contains(httpResponse.statusCode) else {
                    errorMessage = "Server-Fehler: Status Code \(httpResponse.statusCode)"
                    return
                }
                
                guard let data = data else {
                    errorMessage = "Keine Daten vom Server empfangen"
                    return
                }
                
                do {
                    resultData = try JSONDecoder().decode(APIResponse.self, from: data)
                } catch {
                    if let dataString = String(data: data, encoding: .utf8) {
                        errorMessage = "Fehler beim Verarbeiten der Daten: \(error.localizedDescription)\nServer-Antwort: \(dataString)"
                    } else {
                        errorMessage = "Fehler beim Verarbeiten der Daten: \(error.localizedDescription)"
                    }
                }
            }
        }.resume()
    }
}

// MARK: - Helper Views

// View for displaying a single package
struct PackageView: View {
    let package: Package
    @State private var isExpanded = false // Controls the expanded/collapsed state
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Package header (always visible)
            Button(action: { isExpanded.toggle() }) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        // Package name
                        Text(package.name)
                            .font(.headline)
                        
                        // Cost and subscription type
                        HStack {
                            Text("Kosten: €\(String(format: "%.2f", package.costInEuro))")
                            Text("(\(package.subscriptionType == "yearly" ? "Jahres-Abo" : "Monats-Abo"))")
                                .foregroundColor(.gray)
                        }
                        
                        // Active months (if any)
                        if !package.activeMonths.isEmpty {
                            Text("Aktive Monate: \(package.activeMonths.joined(separator: ", "))")
                                .font(.subheadline)
                                .foregroundColor(.blue)
                        }
                        
                        Text("Anzahl Spiele: \(package.gamesCovered.count)")
                    }
                    
                    Spacer()
                    
                    // Expand/collapse indicator
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .foregroundColor(.blue)
                }
            }
            .buttonStyle(PlainButtonStyle())
            
            // Expandable games list
            if isExpanded && !package.gamesCovered.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Abgedeckte Spiele:")
                        .font(.subheadline)
                        .padding(.top, 4)
                    
                    ForEach(package.gamesCovered, id: \.date) { game in
                        GameRow(game: game)
                    }
                }
                .transition(.opacity)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.gray.opacity(0.1))
        .cornerRadius(10)
        .padding(.horizontal)
        .animation(.easeInOut, value: isExpanded)
    }
}

// View for displaying a single game
struct GameRow: View {
    let game: Game
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // Teams
            HStack {
                Image(systemName: "sportscourt")
                    .foregroundColor(.blue)
                Text("\(game.homeTeam) vs \(game.awayTeam)")
                    .font(.system(size: 15))
            }
            
            // Date
            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(.gray)
                Text(formatDate(game.date))
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
            }
            
            // Tournament
            HStack {
                Image(systemName: "trophy")
                    .foregroundColor(.gray)
                Text(game.tournament)
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
            }
            
            Divider()
        }
        .padding(.vertical, 4)
    }
    
    // Helper function to format the date string
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
        
        guard let date = formatter.date(from: dateString) else { return dateString }
        
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

// View for displaying the summary
struct SummaryView: View {
    let data: APIData
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Zusammenfassung")
                .font(.headline)
            Text("Gesamtkosten: €\(String(format: "%.2f", data.total_cost))")
            Text("Abdeckung: \(data.coverage_ratio)")
            Text("Gewichtete Abdeckung: \(data.weighted_coverage)")
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.blue.opacity(0.1))
        .cornerRadius(10)
        .padding(.horizontal)
    }
}

// View for displaying unstreamable games
struct UnstreamableGamesView: View {
    let games: [Game]
    
    var body: some View {
        if !games.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                // Warning header
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.yellow)
                    Text("Nicht streambare Spiele")
                        .font(.headline)
                }
                
                // List of unstreamable games
                ForEach(games, id: \.date) { game in
                    Text("\(game.homeTeam) vs \(game.awayTeam)")
                        .font(.subheadline)
                    Text("\(game.tournament) - \(formatDate(game.date))")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.yellow.opacity(0.1))
            .cornerRadius(10)
            .padding(.horizontal)
        }
    }
    
    // Helper function to format the date string
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
        
        guard let date = formatter.date(from: dateString) else { return dateString }
        
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}
