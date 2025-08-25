import SwiftUI
import MapKit

struct TerritoryDrawingView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 34.2257, longitude: -77.9447),
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )

    @State private var isDrawingMode = false
    @State private var currentTerritoryName = ""
    @State private var selectedSalesperson: SalesPerson?
    @State private var showingNameDialog = false
    @State private var drawnPoints: [CLLocationCoordinate2D] = []
    @State private var territories: [Territory] = []

    var body: some View {
        VStack {
            // Controls Header
            VStack(spacing: 12) {
                Text("Territory Management")
                    .font(.title2)
                    .fontWeight(.bold)

                // Drawing Controls
                HStack {
                    Button(action: {
                        if isDrawingMode {
                            finishDrawing()
                        } else {
                            startDrawing()
                        }
                    }) {
                        HStack {
                            Image(systemName: isDrawingMode ? "checkmark.circle.fill" : "pencil.circle")
                            Text(isDrawingMode ? "Finish Territory" : "Draw Territory")
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(isDrawingMode ? Color.green : Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                    }

                    if isDrawingMode {
                        Button("Cancel") {
                            cancelDrawing()
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.red)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                    }

                    Spacer()
                }

                // Salesperson Selection
                if !isDrawingMode {
                    HStack {
                        Text("Assign to:")
                            .font(.headline)

                        Picker("Salesperson", selection: $selectedSalesperson) {
                            Text("Select Salesperson").tag(nil as SalesPerson?)
                            ForEach(dataManager.salespeople) { person in
                                Text(person.name).tag(person as SalesPerson?)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                    }
                }
            }
            .padding()
            .background(Color(.systemGray6))

            // Map with Territory Drawing
            ZStack {
                Map(coordinateRegion: $region, annotationItems: dataManager.houses) { house in
                    MapAnnotation(coordinate: house.coordinate) {
                        HouseAnnotationView(house: house) {
                            // House tap action
                        }
                    }
                }
                .onTapGesture { location in
                    if isDrawingMode {
                        addPointToTerritory(at: location)
                    }
                }

                // Territory Overlay
                TerritoryOverlayView(territories: territories, drawnPoints: drawnPoints)
            }

            // Territory List
            if !territories.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Existing Territories")
                        .font(.headline)
                        .padding(.horizontal)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(territories) { territory in
                                TerritoryCard(territory: territory, onDelete: {
                                    deleteTerritory(territory)
                                })
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                .background(Color(.systemGray6))
            }
        }
        .navigationTitle("Territory Drawing")
        .alert("Territory Name", isPresented: $showingNameDialog) {
            TextField("Enter territory name", text: $currentTerritoryName)
            Button("Create") {
                createTerritory()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("Give this territory a name")
        }
    }

    // MARK: - Territory Drawing Functions

    private func startDrawing() {
        isDrawingMode = true
        drawnPoints = []
    }

    private func addPointToTerritory(at location: CGPoint) {
        // Convert screen location to map coordinate
        // This is a simplified implementation - in production you'd need proper coordinate conversion
        let coordinate = region.center
        drawnPoints.append(coordinate)
    }

    private func finishDrawing() {
        guard drawnPoints.count >= 3 else {
            // Need at least 3 points to make a territory
            return
        }

        showingNameDialog = true
    }

    private func cancelDrawing() {
        isDrawingMode = false
        drawnPoints = []
    }

    private func createTerritory() {
        guard !currentTerritoryName.isEmpty,
              !drawnPoints.isEmpty,
              let salesperson = selectedSalesperson else {
            return
        }

        let newTerritory = Territory(
            name: currentTerritoryName,
            salespersonId: salesperson.id,
            salespersonName: salesperson.name,
            boundaries: drawnPoints,
            color: Territory.randomColor()
        )

        territories.append(newTerritory)

        // Reset drawing state
        isDrawingMode = false
        drawnPoints = []
        currentTerritoryName = ""

        // Save to backend
        saveTerritory(newTerritory)
    }

    private func deleteTerritory(_ territory: Territory) {
        territories.removeAll { $0.id == territory.id }
    }

    private func saveTerritory(_ territory: Territory) {
        // TODO: Save to Big Beautiful Program via API
        print("Saving territory: \(territory.name)")
    }
}

// MARK: - Supporting Views

struct TerritoryOverlayView: View {
    let territories: [Territory]
    let drawnPoints: [CLLocationCoordinate2D]

    var body: some View {
        // This would render territory polygons on the map
        // Simplified implementation for now
        EmptyView()
    }
}

struct TerritoryCard: View {
    let territory: Territory
    let onDelete: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Circle()
                    .fill(territory.color)
                    .frame(width: 12, height: 12)

                Text(territory.name)
                    .font(.headline)
                    .lineLimit(1)

                Spacer()

                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .foregroundColor(.red)
                }
            }

            Text(territory.salespersonName)
                .font(.caption)
                .foregroundColor(.secondary)

            Text("\(territory.boundaries.count) points")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(8)
        .background(Color(.systemBackground))
        .cornerRadius(8)
        .shadow(radius: 2)
        .frame(width: 120)
    }
}

// MARK: - Territory Model

struct Territory: Identifiable, Codable {
    let id = UUID()
    let name: String
    let salespersonId: UUID
    let salespersonName: String
    let boundaries: [CLLocationCoordinate2D]
    let color: Color
    let createdAt = Date()

    static func randomColor() -> Color {
        let colors: [Color] = [.blue, .red, .green, .orange, .purple, .pink, .yellow]
        return colors.randomElement() ?? .blue
    }
}

// Make CLLocationCoordinate2D Codable
extension CLLocationCoordinate2D: Codable {
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(latitude, forKey: .latitude)
        try container.encode(longitude, forKey: .longitude)
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let latitude = try container.decode(Double.self, forKey: .latitude)
        let longitude = try container.decode(Double.self, forKey: .longitude)
        self.init(latitude: latitude, longitude: longitude)
    }

    private enum CodingKeys: String, CodingKey {
        case latitude, longitude
    }
}

// Make Color Codable (simplified)
extension Color: Codable {
    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode("blue") // Simplified for now
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        let colorName = try container.decode(String.self)
        self = .blue // Simplified for now
    }
}

struct TerritoryDrawingView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            TerritoryDrawingView()
                .environmentObject(DataManager())
        }
    }
}
