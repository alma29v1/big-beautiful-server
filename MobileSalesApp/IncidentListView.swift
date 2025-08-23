import SwiftUI

struct IncidentListView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var selectedType: IncidentType? = nil
    @State private var selectedIncident: Incident?
    @State private var showingIncidentMap = false

    var filteredIncidents: [Incident] {
        var incidents = dataManager.activeIncidents()

        if let type = selectedType {
            incidents = incidents.filter { $0.incidentType == type }
        }

        return incidents.sorted { $0.createdAt > $1.createdAt }
    }

    var body: some View {
        VStack {
                // Statistics
                HStack {
                    StatCard(title: "Active", value: "\(dataManager.activeIncidentsCount)", color: .red)
                    StatCard(title: "Total", value: "\(dataManager.incidents.count)", color: .orange)
                }
                .padding(.horizontal)

                // Type filter
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        FilterChip(title: "All", isSelected: selectedType == nil) {
                            selectedType = nil
                        }

                        ForEach(IncidentType.allCases, id: \.self) { type in
                            FilterChip(title: type.displayName, isSelected: selectedType == type) {
                                selectedType = type
                            }
                        }
                    }
                    .padding(.horizontal)
                }

                // Incident list
                List(filteredIncidents) { incident in
                    IncidentRowView(incident: incident) {
                        selectedIncident = incident
                        showingIncidentMap = true
                    }
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Incidents")
            .sheet(isPresented: $showingIncidentMap) {
                if let incident = selectedIncident {
                    NavigationView {
                        IncidentMapView(incident: incident)
                            .environmentObject(dataManager)
                            .navigationTitle("Incident Location")
                            .navigationBarTitleDisplayMode(.inline)
                            .toolbar {
                                ToolbarItem(placement: .navigationBarTrailing) {
                                    Button("Done") {
                                        showingIncidentMap = false
                                    }
                                }
                            }
                    }
                }
            }
        }
}

struct IncidentRowView: View {
    let incident: Incident
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack {
                // Incident icon
                ZStack {
                    Circle()
                        .fill(incidentColor)
                        .frame(width: 40, height: 40)

                    Image(systemName: incident.iconName)
                        .foregroundColor(.white)
                        .font(.title3)
                }

                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(incident.incidentType.displayName)
                            .font(.headline)
                            .foregroundColor(.primary)

                        Spacer()

                        Text(incident.status.displayName)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(statusColor.opacity(0.2))
                            .foregroundColor(statusColor)
                            .cornerRadius(8)
                    }

                    Text(incident.address)
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    Text(incident.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)

                    if let assignedSalesperson = getAssignedSalesperson() {
                        HStack {
                            Image(systemName: "person.fill")
                                .font(.caption2)
                                .foregroundColor(.blue)

                            Text("Assigned: \(assignedSalesperson.name)")
                                .font(.caption)
                                .foregroundColor(.blue)
                        }
                    }
                }

                Spacer()

                // Map icon
                Image(systemName: "map")
                    .foregroundColor(.blue)
                    .font(.caption)
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(PlainButtonStyle())
    }

    private var incidentColor: Color {
        switch incident.incidentType {
        case .fire:
            return .red
        case .breakIn:
            return .orange
        case .flood:
            return .blue
        case .storm:
            return .purple
        case .theft:
            return .yellow
        }
    }

    private var statusColor: Color {
        switch incident.status {
        case .active:
            return .red
        case .responded:
            return .orange
        case .resolved:
            return .green
        }
    }

    private func getAssignedSalesperson() -> SalesPerson? {
        // In a real app, you'd get this from the data manager
        return nil
    }
}

struct IncidentListView_Previews: PreviewProvider {
    static var previews: some View {
        IncidentListView()
            .environmentObject(DataManager())
    }
}
