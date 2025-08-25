import SwiftUI
import MapKit

struct SalesContextView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var searchAddress = ""
    @State private var incidentContext: IncidentContextResponse?
    @State private var recentIncidents: [RecentIncident] = []
    @State private var isLoading = false
    @State private var currentLocation: CLLocationCoordinate2D?
    @State private var selectedHouse: House?
    @State private var showingVisitTracker = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header with Address Search
                VStack(spacing: 16) {
                    Text("Sales Context Engine")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("Get incident-driven talking points for every door knock")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                    
                    // Address Search
                    HStack {
                        Image(systemName: "magnifyingglass")
                            .foregroundColor(.secondary)
                        
                        TextField("Enter address to get sales context...", text: $searchAddress)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .onSubmit {
                                searchForIncidentContext()
                            }
                        
                        Button("Search") {
                            searchForIncidentContext()
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                        .disabled(searchAddress.isEmpty || isLoading)
                    }
                }
                .padding()
                .background(Color(.systemGray6))
                
                if isLoading {
                    Spacer()
                    VStack(spacing: 16) {
                        ProgressView()
                            .scaleEffect(1.5)
                        Text("Analyzing local incidents...")
                            .font(.headline)
                        Text("Getting your targeted talking points")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                } else if let context = incidentContext {
                    // Sales Context Results
                    ScrollView {
                        VStack(spacing: 20) {
                            // Urgency Score
                            UrgencyScoreCard(context: context)
                            
                            // Talking Points
                            TalkingPointsCard(context: context)
                            
                            // Product Recommendations
                            ProductRecommendationsCard(context: context)
                            
                            // Objection Responses
                            ObjectionResponsesCard(context: context)
                            
                            // Conversation Starters
                            ConversationStartersCard(context: context)
                            
                            // Visit Tracking
                            VisitTrackingCard(address: context.address) {
                                showingVisitTracker = true
                            }
                        }
                        .padding()
                    }
                } else {
                    // Quick Access to Houses
                    VStack {
                        Text("Quick Access")
                            .font(.headline)
                            .padding(.top)
                        
                        Text("Tap any house to get instant sales context")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .padding(.bottom)
                        
                        List(dataManager.houses.prefix(10), id: \.id) { house in
                            HouseQuickAccessRow(house: house) {
                                searchAddress = house.address
                                searchForIncidentContext()
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Sales Context")
        .onAppear {
            loadRecentIncidents()
        }
        .sheet(isPresented: $showingVisitTracker) {
            VisitTrackerView(address: incidentContext?.address ?? searchAddress)
                .environmentObject(dataManager)
        }
    }
    
    private func searchForIncidentContext() {
        guard !searchAddress.isEmpty else { return }
        
        isLoading = true
        
        Task {
            do {
                let context = try await dataManager.bigBeautifulAPIClient.getIncidentContext(for: searchAddress)
                
                await MainActor.run {
                    self.incidentContext = context
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    print("Failed to get incident context: \(error)")
                }
            }
        }
    }
    
    private func loadRecentIncidents() {
        Task {
            do {
                let incidents = try await dataManager.bigBeautifulAPIClient.getRecentIncidents()
                
                await MainActor.run {
                    self.recentIncidents = incidents.recentIncidents
                }
            } catch {
                print("Failed to load recent incidents: \(error)")
            }
        }
    }
}

// MARK: - Supporting Views

struct UrgencyScoreCard: View {
    let context: IncidentContextResponse
    
    var urgencyColor: Color {
        switch context.urgencyScore {
        case 1...3: return .green
        case 4...6: return .orange
        case 7...8: return .red
        case 9...10: return .purple
        default: return .gray
        }
    }
    
    var urgencyLevel: String {
        switch context.urgencyScore {
        case 1...3: return "Low Priority"
        case 4...6: return "Medium Priority"
        case 7...8: return "High Priority"
        case 9...10: return "Urgent"
        default: return "Unknown"
        }
    }
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(urgencyColor)
                
                Text("Urgency Assessment")
                    .font(.headline)
                
                Spacer()
                
                Text("\(context.urgencyScore)/10")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(urgencyColor)
            }
            
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(urgencyLevel)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(urgencyColor)
                    
                    Text("Primary incident: \(context.primaryIncidentType.capitalized)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Text("\(context.incidentsWithinMile) incidents")
                        .font(.caption)
                        .fontWeight(.semibold)
                    
                    Text("within 1 mile")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct TalkingPointsCard: View {
    let context: IncidentContextResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "quote.bubble.fill")
                    .foregroundColor(.blue)
                
                Text("Talking Points")
                    .font(.headline)
                
                Spacer()
                
                Image(systemName: "doc.on.doc")
                    .foregroundColor(.blue)
            }
            
            ForEach(Array(context.talkingPoints.enumerated()), id: \.offset) { index, point in
                HStack(alignment: .top, spacing: 8) {
                    Text("\(index + 1).")
                        .font(.caption)
                        .fontWeight(.bold)
                        .foregroundColor(.blue)
                        .frame(width: 20, alignment: .leading)
                    
                    Text(point)
                        .font(.body)
                        .multilineTextAlignment(.leading)
                    
                    Spacer()
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct ProductRecommendationsCard: View {
    let context: IncidentContextResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "shield.checkered")
                    .foregroundColor(.green)
                
                Text("Product Recommendations")
                    .font(.headline)
                
                Spacer()
            }
            
            ForEach(context.productRecommendations, id: \.product) { recommendation in
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(recommendation.product)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        
                        Text(recommendation.reason)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Text(recommendation.priority.uppercased())
                        .font(.caption)
                        .fontWeight(.bold)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(recommendation.priority == "high" ? Color.red.opacity(0.2) : Color.orange.opacity(0.2))
                        .foregroundColor(recommendation.priority == "high" ? .red : .orange)
                        .cornerRadius(4)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct ObjectionResponsesCard: View {
    let context: IncidentContextResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "message.fill")
                    .foregroundColor(.orange)
                
                Text("Objection Responses")
                    .font(.headline)
                
                Spacer()
            }
            
            ForEach(context.objectionResponses.sorted(by: { $0.key < $1.key }), id: \.key) { objection, response in
                VStack(alignment: .leading, spacing: 4) {
                    Text("\"" + objection.replacingOccurrences(of: "_", with: " ").capitalized + "\"")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(.orange)
                    
                    Text(response)
                        .font(.body)
                        .foregroundColor(.primary)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct ConversationStartersCard: View {
    let context: IncidentContextResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "person.2.fill")
                    .foregroundColor(.purple)
                
                Text("Conversation Starters")
                    .font(.headline)
                
                Spacer()
            }
            
            ForEach(Array(context.conversationStarters.enumerated()), id: \.offset) { index, starter in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: "quote.opening")
                            .font(.caption)
                            .foregroundColor(.purple)
                        
                        Text("Option \(index + 1)")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.purple)
                        
                        Spacer()
                    }
                    
                    Text(starter)
                        .font(.body)
                        .italic()
                        .padding(.leading, 16)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct VisitTrackingCard: View {
    let address: String
    let onTrackVisit: () -> Void
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
                
                Text("Ready to Visit")
                    .font(.headline)
                
                Spacer()
            }
            
            Text("Track your visit progress and update contact status")
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Button(action: onTrackVisit) {
                HStack {
                    Image(systemName: "plus.circle.fill")
                    Text("Start Visit")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.green)
                .foregroundColor(.white)
                .cornerRadius(8)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct HouseQuickAccessRow: View {
    let house: House
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(house.address)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text("\(house.city), \(house.state)")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Image(systemName: "arrow.right.circle.fill")
                    .foregroundColor(.blue)
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct SalesContextView_Previews: PreviewProvider {
    static var previews: some View {
        SalesContextView()
            .environmentObject(DataManager())
    }
}
