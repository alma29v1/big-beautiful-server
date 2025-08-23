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
        VStack {
            Text("INCIDENT MAP VIEW IS WORKING!")
                .font(.title)
                .foregroundColor(.red)
                .padding()

            Text("Incident Type: \(incident.incidentType.displayName)")
                .font(.headline)
                .padding()

            Text("Address: \(incident.address)")
                .font(.body)
                .padding()

            Text("Status: \(incident.status.displayName)")
                .font(.body)
                .padding()

            Spacer()

            Button("Get Directions") {
                openInMaps()
            }
            .font(.title2)
            .foregroundColor(.white)
            .padding()
            .background(Color.blue)
            .cornerRadius(10)

            Button("Call Emergency") {
                callEmergencyServices()
            }
            .font(.title2)
            .foregroundColor(.white)
            .padding()
            .background(Color.red)
            .cornerRadius(10)

            Spacer()
        }
        .background(Color.yellow)
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
