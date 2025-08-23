import Foundation

// MARK: - API Models

struct Contact: Codable, Identifiable {
    let id: Int
    let address: String
    let city: String
    let state: String
    let zipCode: String
    let ownerName: String
    let ownerEmail: String
    let ownerPhone: String
    let fiberAvailable: Bool
    let createdDate: String
    let source: String

    enum CodingKeys: String, CodingKey {
        case id, address, city, state, source
        case zipCode = "zip_code"
        case ownerName = "owner_name"
        case ownerEmail = "owner_email"
        case ownerPhone = "owner_phone"
        case fiberAvailable = "fiber_available"
        case createdDate = "created_date"
    }
}

struct ContactResponse: Codable {
    let contacts: [Contact]
    let total: Int
    let success: Bool
}

struct FiberCheck: Codable {
    let address: String
}

struct FiberResponse: Codable {
    let address: String
    let fiberAvailable: Bool
    let speedTiers: [String]
    let installationDate: String?
    let status: String
    let estimatedInstallationTime: String?
    let promotionalOffers: [PromotionalOffer]

    enum CodingKeys: String, CodingKey {
        case address, status
        case fiberAvailable = "fiber_available"
        case speedTiers = "speed_tiers"
        case installationDate = "installation_date"
        case estimatedInstallationTime = "estimated_installation_time"
        case promotionalOffers = "promotional_offers"
    }
}

struct PromotionalOffer: Codable {
    let speed: String
    let price: String
    let term: String
}

struct AnalyticsResponse: Codable {
    let totalContacts: Int
    let fiberContacts: Int
    let recentContacts: Int
    let conversionRate: Double
    let weeklyGrowth: Double
    let topCities: [CityData]
    let timestamp: String

    enum CodingKeys: String, CodingKey {
        case timestamp
        case totalContacts = "total_contacts"
        case fiberContacts = "fiber_contacts"
        case recentContacts = "recent_contacts"
        case conversionRate = "conversion_rate"
        case weeklyGrowth = "weekly_growth"
        case topCities = "top_cities"
    }
}

struct CityData: Codable {
    let city: String
    let count: Int
}

struct GeocodeRequest: Codable {
    let address: String
}

struct GeocodeResponse: Codable {
    let latitude: Double
    let longitude: Double
    let formattedAddress: String
    let success: Bool

    enum CodingKeys: String, CodingKey {
        case latitude, longitude, success
        case formattedAddress = "formatted_address"
    }
}

// MARK: - Email Campaign Models

struct EmailCampaign: Codable, Identifiable {
    let id: Int
    let name: String
    let subject: String
    let status: String
    let sentDate: String?
    let totalRecipients: Int
    let openRate: Double
    let clickRate: Double
    let bounceRate: Double
    let unsubscribeRate: Double
    let opens: Int
    let clicks: Int
    let bounces: Int
    let unsubscribes: Int

    enum CodingKeys: String, CodingKey {
        case id, name, subject, status, opens, clicks, bounces, unsubscribes
        case sentDate = "sent_date"
        case totalRecipients = "total_recipients"
        case openRate = "open_rate"
        case clickRate = "click_rate"
        case bounceRate = "bounce_rate"
        case unsubscribeRate = "unsubscribe_rate"
    }
}

struct EmailCampaignResponse: Codable {
    let campaigns: [EmailCampaign]
    let total: Int
    let success: Bool
}

struct EmailStats: Codable {
    let totalCampaigns: Int
    let totalSent: Int
    let averageOpenRate: Double
    let averageClickRate: Double
    let totalOpens: Int
    let totalClicks: Int
    let recentCampaigns: [EmailCampaign]

    enum CodingKeys: String, CodingKey {
        case recentCampaigns = "recent_campaigns"
        case totalCampaigns = "total_campaigns"
        case totalSent = "total_sent"
        case averageOpenRate = "average_open_rate"
        case averageClickRate = "average_click_rate"
        case totalOpens = "total_opens"
        case totalClicks = "total_clicks"
    }
}

struct EmailRecipient: Codable, Identifiable {
    let id: Int
    let email: String
    let name: String?
    let status: String
    let openedAt: String?
    let clickedAt: String?
    let bounced: Bool
    let unsubscribed: Bool

    enum CodingKeys: String, CodingKey {
        case id, email, name, status, bounced, unsubscribed
        case openedAt = "opened_at"
        case clickedAt = "clicked_at"
    }
}

// MARK: - Server Configuration Models

struct ServerConfig {
    let name: String
    let host: String
    let port: String
    let priority: Int
}

struct ServerTestResult {
    let config: ServerConfig
    let isAvailable: Bool
    let error: String?
}

// MARK: - API Errors

enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case decodingError
    case networkError

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let code):
            return "Server error: \(code)"
        case .decodingError:
            return "Failed to decode response"
        case .networkError:
            return "Network error"
        }
    }
}

// MARK: - Big Beautiful API Client

class BigBeautifulAPIClient: ObservableObject {
    @Published var baseURL = "http://localhost:5001/api"
    @Published var serverHost = "localhost"
    @Published var serverPort = "5001"
    @Published var currentServerIndex = 0
    @Published var connectionStatus = "Disconnected"
    // API Key should be set in environment variables or configuration
    // For production, this should be stored securely
    let apiKey = "YOUR_API_KEY_HERE" // Replace with actual key when deploying

    @Published var isLoading = false
    @Published var error: String?

    // Redundant server configuration
    private let serverConfigurations = [
        ServerConfig(name: "Replit Cloud", host: "big-beautiful-server.alma29v1.repl.co", port: "443", priority: 1),
        ServerConfig(name: "Local Network", host: "192.168.84.130", port: "5001", priority: 2),
        ServerConfig(name: "Internet Access", host: "65.190.137.27", port: "5001", priority: 3),
        ServerConfig(name: "Localhost", host: "127.0.0.1", port: "5001", priority: 4)
    ]

    init() {
        loadServerSettings()
        updateBaseURL()
    }

    func updateServerSettings(host: String, port: String) {
        serverHost = host
        serverPort = port
        updateBaseURL()
        saveServerSettings()
    }

    private func updateBaseURL() {
        // Use HTTPS for Replit, HTTP for local servers
        let urlProtocol = serverHost.contains("repl.co") ? "https" : "http"
        baseURL = "\(urlProtocol)://\(serverHost):\(serverPort)/api"
    }

    private func saveServerSettings() {
        UserDefaults.standard.set(serverHost, forKey: "serverHost")
        UserDefaults.standard.set(serverPort, forKey: "serverPort")
        UserDefaults.standard.set(currentServerIndex, forKey: "currentServerIndex")
    }

    private func loadServerSettings() {
        // Load saved settings or default to first server
        serverHost = UserDefaults.standard.string(forKey: "serverHost") ?? serverConfigurations[0].host
        serverPort = UserDefaults.standard.string(forKey: "serverPort") ?? serverConfigurations[0].port
        currentServerIndex = UserDefaults.standard.integer(forKey: "currentServerIndex")
        updateBaseURL()
    }

    // MARK: - Redundant Connection Methods

    func connectWithFallback() async -> Bool {
        for (index, config) in serverConfigurations.enumerated() {
            do {
                print("🔄 Trying server \(index + 1)/\(serverConfigurations.count): \(config.name) (\(config.host):\(config.port))")

                // Use HTTPS for Replit, HTTP for local servers
                let urlProtocol = config.host.contains("repl.co") ? "https" : "http"
                let testURL = "\(urlProtocol)://\(config.host):\(config.port)/api/health"
                guard let url = URL(string: testURL) else { continue }

                var request = URLRequest(url: url)
                request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
                request.timeoutInterval = 5.0 // 5 second timeout

                let (_, response) = try await URLSession.shared.data(for: request)

                if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                    print("✅ Connected to \(config.name): \(config.host):\(config.port)")

                    await MainActor.run {
                        self.serverHost = config.host
                        self.serverPort = config.port
                        self.currentServerIndex = index
                        self.connectionStatus = "Connected to \(config.name)"
                        self.updateBaseURL()
                        self.saveServerSettings()
                    }

                    return true
                }
            } catch {
                print("❌ Failed to connect to \(config.name): \(error.localizedDescription)")
                continue
            }
        }

        await MainActor.run {
            self.connectionStatus = "All servers failed"
            self.error = "Unable to connect to any server"
        }

        return false
    }

    func testAllServers() async -> [ServerTestResult] {
        var results: [ServerTestResult] = []

        for config in serverConfigurations {
            let result = await testServer(config)
            results.append(result)
        }

        return results
    }

    private func testServer(_ config: ServerConfig) async -> ServerTestResult {
        do {
            // Use HTTPS for Replit, HTTP for local servers
            let urlProtocol = config.host.contains("repl.co") ? "https" : "http"
            let testURL = "\(urlProtocol)://\(config.host):\(config.port)/api/health"
            guard let url = URL(string: testURL) else {
                return ServerTestResult(config: config, isAvailable: false, error: "Invalid URL")
            }

            var request = URLRequest(url: url)
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
            request.timeoutInterval = 3.0

            let (_, response) = try await URLSession.shared.data(for: request)

            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 200 {
                    return ServerTestResult(config: config, isAvailable: true, error: nil)
                } else {
                    return ServerTestResult(config: config, isAvailable: false, error: "HTTP \(httpResponse.statusCode)")
                }
            } else {
                return ServerTestResult(config: config, isAvailable: false, error: "Invalid response")
            }
        } catch {
            return ServerTestResult(config: config, isAvailable: false, error: error.localizedDescription)
        }
    }

    func makeRequest<T: Codable>(endpoint: String, method: String, body: Data? = nil) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let body = body {
            request.httpBody = body
        }

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw APIError.serverError(httpResponse.statusCode)
        }

        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            print("Decoding error: \(error)")
            throw APIError.decodingError
        }
    }

    // MARK: - API Methods

    func getContacts() async throws -> ContactResponse {
        return try await makeRequest(endpoint: "/contacts", method: "GET")
    }

    func getContact(id: Int) async throws -> Contact {
        return try await makeRequest(endpoint: "/contacts/\(id)", method: "GET")
    }

    func createContact(address: String, city: String, state: String, zipCode: String,
                      ownerName: String, ownerEmail: String, ownerPhone: String, fiberAvailable: Bool) async throws -> Contact {
        let contactData = [
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zipCode,
            "owner_name": ownerName,
            "owner_email": ownerEmail,
            "owner_phone": ownerPhone,
            "fiber_available": fiberAvailable
        ] as [String : Any]

        let body = try JSONSerialization.data(withJSONObject: contactData)
        return try await makeRequest(endpoint: "/contacts", method: "POST", body: body)
    }

    func checkATTFiber(address: String) async throws -> FiberResponse {
        let fiberCheck = FiberCheck(address: address)
        let body = try JSONEncoder().encode(fiberCheck)
        return try await makeRequest(endpoint: "/att-fiber-check", method: "POST", body: body)
    }

    func geocodeAddress(address: String) async throws -> GeocodeResponse {
        let geocodeRequest = GeocodeRequest(address: address)
        let body = try JSONEncoder().encode(geocodeRequest)
        return try await makeRequest(endpoint: "/geocode", method: "POST", body: body)
    }

    func getAnalytics() async throws -> AnalyticsResponse {
        return try await makeRequest(endpoint: "/analytics", method: "GET")
    }

    func healthCheck() async throws -> [String: String] {
        return try await makeRequest(endpoint: "/health", method: "GET")
    }

    // MARK: - Additional API Methods

    func syncData() async throws -> [String: String] {
        return try await makeRequest(endpoint: "/sync", method: "POST")
    }

    func getRollingSales() async throws -> [String: String] {
        return try await makeRequest(endpoint: "/rolling-sales", method: "GET")
    }

    func exportRollingSales() async throws -> [String: String] {
        return try await makeRequest(endpoint: "/rolling-sales/export", method: "GET")
    }

    // MARK: - Territory Management Methods

    func getTerritories() async throws -> [String: String] {
        return try await makeRequest(endpoint: "/territories", method: "GET")
    }

    func getTerritory(id: Int) async throws -> [String: String] {
        return try await makeRequest(endpoint: "/territories/\(id)", method: "GET")
    }

    func createTerritory(territoryData: [String: String]) async throws -> [String: String] {
        let body = try JSONSerialization.data(withJSONObject: territoryData)
        return try await makeRequest(endpoint: "/territories", method: "POST", body: body)
    }

    func updateTerritory(id: Int, territoryData: [String: String]) async throws -> [String: String] {
        let body = try JSONSerialization.data(withJSONObject: territoryData)
        return try await makeRequest(endpoint: "/territories/\(id)", method: "PUT", body: body)
    }

    func deleteTerritory(id: Int) async throws -> [String: String] {
        return try await makeRequest(endpoint: "/territories/\(id)", method: "DELETE")
    }

    func getTerritoryLeads(territoryId: Int) async throws -> [String: String] {
        return try await makeRequest(endpoint: "/territories/\(territoryId)/leads", method: "GET")
    }

    func assignLeadsToTerritory(territoryId: Int, leadsData: [String: String]) async throws -> [String: String] {
        let body = try JSONSerialization.data(withJSONObject: leadsData)
        return try await makeRequest(endpoint: "/territories/\(territoryId)/leads", method: "POST", body: body)
    }

    func exportTerritoryLeads(territoryId: Int) async throws -> [String: String] {
        return try await makeRequest(endpoint: "/territories/\(territoryId)/export", method: "GET")
    }
}
