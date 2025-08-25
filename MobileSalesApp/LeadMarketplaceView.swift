import SwiftUI

struct LeadMarketplaceView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var availableLeads: [Lead] = []
    @State private var soldLeads: [Lead] = []
    @State private var selectedLead: Lead?
    @State private var showingPurchaseConfirmation = false
    @State private var isLoadingLeads = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            VStack(spacing: 16) {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Lead Marketplace")
                            .font(.title)
                            .fontWeight(.bold)
                        
                        Text("Monetize your leads and grow your business")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Button("Refresh") {
                        loadAvailableLeads()
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(8)
                }
                
                // Marketplace Stats
                HStack(spacing: 20) {
                    MarketplaceStatCard(title: "Available Leads", value: "\(availableLeads.count)", icon: "house.circle")
                    MarketplaceStatCard(title: "Sold This Week", value: "\(soldLeads.count)", icon: "dollarsign.circle.fill")
                    MarketplaceStatCard(title: "Revenue", value: "$\(totalRevenue)", icon: "chart.line.uptrend.xyaxis")
                }
            }
            .padding()
            .background(Color(.systemGray6))
            
            if isLoadingLeads {
                Spacer()
                ProgressView("Loading leads...")
                Spacer()
            } else {
                // Available Leads List
                List {
                    Section(header: Text("Available Leads")) {
                        ForEach(availableLeads) { lead in
                            LeadRowView(lead: lead) {
                                selectedLead = lead
                                showingPurchaseConfirmation = true
                            }
                        }
                    }
                    
                    if !soldLeads.isEmpty {
                        Section(header: Text("Recently Sold")) {
                            ForEach(soldLeads) { lead in
                                SoldLeadRowView(lead: lead)
                            }
                        }
                    }
                }
            }
        }
        .onAppear {
            loadAvailableLeads()
        }
        .alert("Purchase Lead", isPresented: $showingPurchaseConfirmation) {
            if let lead = selectedLead {
                Button("Purchase for $\(lead.price, specifier: "%.0f")") {
                    purchaseLead(lead)
                }
                Button("Cancel", role: .cancel) { }
            }
        } message: {
            if let lead = selectedLead {
                Text("Are you sure you want to purchase this lead for $\(lead.price, specifier: "%.0f")?")
            }
        }
    }
    
    private var totalRevenue: Int {
        soldLeads.reduce(0) { $0 + Int($1.price) }
    }
    
    private func loadAvailableLeads() {
        isLoadingLeads = true
        
        // Simulate loading from Big Beautiful Program
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            // Mock leads for now - these would come from real appointments/responses
            availableLeads = [
                Lead(
                    id: UUID(),
                    address: "123 Ocean View Dr, Wilmington, NC",
                    contactName: "John Smith",
                    contactPhone: "910-555-0101",
                    leadType: .appointmentScheduled,
                    description: "Homeowner scheduled ADT consultation after break-in in neighborhood",
                    priority: .high,
                    price: 45.0,
                    createdAt: Date(),
                    sourceIncident: "Break-in nearby"
                ),
                Lead(
                    id: UUID(),
                    address: "456 Coastal Blvd, Leland, NC",
                    contactName: "Sarah Johnson",
                    contactPhone: "910-555-0202",
                    leadType: .emailResponse,
                    description: "Responded to email campaign, interested in home security",
                    priority: .medium,
                    price: 25.0,
                    createdAt: Date(),
                    sourceIncident: "Email campaign response"
                ),
                Lead(
                    id: UUID(),
                    address: "789 Harbor Point Way, Southport, NC",
                    contactName: "Mike Davis",
                    contactPhone: "910-555-0303",
                    leadType: .hotLead,
                    description: "House fire in area, wants immediate security consultation",
                    priority: .high,
                    price: 65.0,
                    createdAt: Date(),
                    sourceIncident: "House fire incident"
                )
            ]
            
            soldLeads = [
                Lead(
                    id: UUID(),
                    address: "321 Riverside Ave, Hampstead, NC",
                    contactName: "Emma Wilson",
                    contactPhone: "910-555-0404",
                    leadType: .appointmentScheduled,
                    description: "Scheduled appointment - SOLD to Tom Door",
                    priority: .high,
                    price: 45.0,
                    createdAt: Date().addingTimeInterval(-86400),
                    sourceIncident: "Storm damage"
                )
            ]
            
            isLoadingLeads = false
        }
    }
    
    private func purchaseLead(_ lead: Lead) {
        // Move lead to sold leads
        if let index = availableLeads.firstIndex(where: { $0.id == lead.id }) {
            var soldLead = availableLeads.remove(at: index)
            soldLead.description += " - PURCHASED"
            soldLeads.insert(soldLead, at: 0)
        }
        
        // TODO: Process payment via Apple StoreKit
        // TODO: Notify Big Beautiful Program of purchase
        
        selectedLead = nil
        
        // Show success feedback
        // TODO: Add success animation/feedback
    }
}

// MARK: - Supporting Views

struct MarketplaceStatCard: View {
    let title: String
    let value: String
    let icon: String
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(8)
        .shadow(radius: 2)
    }
}

struct LeadRowView: View {
    let lead: Lead
    let onPurchase: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(lead.contactName)
                        .font(.headline)
                    
                    Text(lead.address)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Text("$\(lead.price, specifier: "%.0f")")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.green)
                    
                    PriorityBadge(priority: lead.priority)
                }
            }
            
            Text(lead.description)
                .font(.body)
                .foregroundColor(.primary)
            
            HStack {
                LeadTypeBadge(type: lead.leadType)
                
                Text(lead.sourceIncident)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Button("Purchase") {
                    onPurchase()
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(6)
            }
        }
        .padding(.vertical, 4)
    }
}

struct SoldLeadRowView: View {
    let lead: Lead
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(lead.contactName)
                    .font(.headline)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("$\(lead.price, specifier: "%.0f")")
                    .font(.title3)
                    .fontWeight(.bold)
                    .foregroundColor(.green)
            }
            
            Text(lead.address)
                .font(.subheadline)
                .foregroundColor(.secondary)
                
            Text("✅ SOLD")
                .font(.caption)
                .fontWeight(.bold)
                .foregroundColor(.green)
        }
        .padding(.vertical, 4)
    }
}

struct PriorityBadge: View {
    let priority: LeadPriority
    
    var body: some View {
        Text(priority.displayName)
            .font(.caption)
            .fontWeight(.semibold)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(priority.color.opacity(0.2))
            .foregroundColor(priority.color)
            .cornerRadius(4)
    }
}

struct LeadTypeBadge: View {
    let type: LeadType
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: type.icon)
            Text(type.displayName)
        }
        .font(.caption)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color.blue.opacity(0.1))
        .foregroundColor(.blue)
        .cornerRadius(4)
    }
}

// MARK: - Lead Models

struct Lead: Identifiable, Codable {
    let id: UUID
    let address: String
    let contactName: String
    let contactPhone: String
    let leadType: LeadType
    var description: String
    let priority: LeadPriority
    let price: Double
    let createdAt: Date
    let sourceIncident: String
}

enum LeadType: String, Codable, CaseIterable {
    case emailResponse = "email_response"
    case appointmentScheduled = "appointment_scheduled"
    case hotLead = "hot_lead"
    case callbackRequest = "callback_request"
    
    var displayName: String {
        switch self {
        case .emailResponse: return "Email Response"
        case .appointmentScheduled: return "Appointment"
        case .hotLead: return "Hot Lead"
        case .callbackRequest: return "Callback"
        }
    }
    
    var icon: String {
        switch self {
        case .emailResponse: return "envelope.fill"
        case .appointmentScheduled: return "calendar"
        case .hotLead: return "flame.fill"
        case .callbackRequest: return "phone.fill"
        }
    }
}

enum LeadPriority: String, Codable, CaseIterable {
    case low, medium, high, urgent
    
    var displayName: String {
        rawValue.capitalized
    }
    
    var color: Color {
        switch self {
        case .low: return .green
        case .medium: return .orange
        case .high: return .red
        case .urgent: return .purple
        }
    }
}

struct LeadMarketplaceView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            LeadMarketplaceView()
                .environmentObject(DataManager())
        }
    }
}
