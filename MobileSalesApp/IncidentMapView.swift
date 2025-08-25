import SwiftUI
import MapKit

struct IncidentMapView: View {
    let incident: Incident
    @EnvironmentObject var dataManager: DataManager
    @State private var region: MKCoordinateRegion

    init(incident: Incident) {
        self.incident = incident
        self._region = State(initialValue: MKCoordinateRegion(
            center: incident.coordinate,
            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
        ))
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header with Incident Type and Status
                VStack {
                    Text(incident.incidentType.displayName)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)

                    Text(incident.status.displayName)
                        .font(.title3)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(statusColor.opacity(0.2))
                        .foregroundColor(statusColor)
                        .cornerRadius(8)
                }
                .padding(.top)

                // Location Section
                Section(header: Text("Location").font(.headline)) {
                    Text(incident.address)
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }

                // Description Section
                Section(header: Text("Description").font(.headline)) {
                    Text(incident.description)
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }

                // Additional Details
                Section(header: Text("Details").font(.headline)) {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Date:")
                                .fontWeight(.semibold)
                            Text(incident.createdAt, style: .date)
                        }
                        HStack {
                            Text("Time:")
                                .fontWeight(.semibold)
                            Text(incident.createdAt, style: .time)
                        }
                        // Add more details if available, e.g.:
                        // Text("Responding Units: Police, Fire Dept")
                        // Text("Notes: High priority incident")
                    }
                    .font(.body)
                    .foregroundColor(.secondary)
                }

                // Action Buttons
                VStack(spacing: 12) {
                    Button("Get Directions") {
                        openInMaps()
                    }
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(10)

                    Button("Call Emergency") {
                        callEmergencyServices()
                    }
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.red)
                    .cornerRadius(10)
                }
                .padding(.horizontal)
            }
            .padding()
        }
        .navigationTitle("Incident Details")
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

    private func openInMaps() {
        let placemark = MKPlacemark(coordinate: incident.coordinate)
        let mapItem = MKMapItem(placemark: placemark)
        mapItem.name = incident.address
        mapItem.openInMaps(launchOptions: [
            MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving
        ])
    }

    private func callEmergencyServices() {
        // In a real app, you might want to call different numbers based on incident type
        let emergencyNumber = "911"
        if let url = URL(string: "tel://\(emergencyNumber)") {
            UIApplication.shared.open(url)
        }
    }
}

struct IncidentMapView_Previews: PreviewProvider {
    static var previews: some View {
        IncidentMapView(incident: Incident(
            address: "123 Main St",
            incidentType: .fire,
            description: "Fire at residential property",
            latitude: 34.2257,
            longitude: -77.9447
        ))
        .environmentObject(DataManager())
    }
}
