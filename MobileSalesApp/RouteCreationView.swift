import SwiftUI
import MapKit

struct RouteCreationView: View {
    let selectedHouses: Set<UUID>
    let allHouses: [House]
    @EnvironmentObject var dataManager: DataManager
    @State private var selectedSalesperson: SalesPerson?
    @State private var routeName = ""
    @State private var showingRouteMap = false
    @State private var createdRoute: Route?

    var selectedHousesList: [House] {
        allHouses.filter { selectedHouses.contains($0.id) }
    }

    var body: some View {
        VStack(spacing: 20) {
            // Route info
            VStack(alignment: .leading, spacing: 12) {
                Text("Create Route")
                    .font(.title2)
                    .fontWeight(.bold)

                Text("Selected \(selectedHousesList.count) houses")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                TextField("Route Name", text: $routeName)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .placeholder(when: routeName.isEmpty) {
                        Text("Enter route name...")
                            .foregroundColor(.gray)
                    }
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(10)

            // Salesperson selection
            VStack(alignment: .leading, spacing: 12) {
                Text("Assign Salesperson")
                    .font(.headline)

                Picker("Salesperson", selection: $selectedSalesperson) {
                    Text("Select salesperson...").tag(nil as SalesPerson?)
                    ForEach(dataManager.salespeople) { person in
                        Text(person.name).tag(person as SalesPerson?)
                    }
                }
                .pickerStyle(MenuPickerStyle())
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(10)

            // Selected houses preview
            VStack(alignment: .leading, spacing: 12) {
                Text("Selected Houses")
                    .font(.headline)

                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(selectedHousesList) { house in
                            HStack {
                                VStack(alignment: .leading) {
                                    Text(house.address)
                                        .font(.subheadline)
                                        .fontWeight(.medium)

                                    Text(house.contactName)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }

                                Spacer()

                                Text(house.status.displayName)
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(statusColor(for: house.status).opacity(0.2))
                                    .foregroundColor(statusColor(for: house.status))
                                    .cornerRadius(8)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
                .frame(maxHeight: 200)
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(10)

            Spacer()

            // Action buttons
            VStack(spacing: 12) {
                Button(action: {
                    showingRouteMap = true
                }) {
                    HStack {
                        Image(systemName: "map")
                        Text("Preview Route")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }

                Button(action: {
                    createRoute()
                }) {
                    HStack {
                        Image(systemName: "plus.circle")
                        Text("Create Route")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(canCreateRoute ? Color.green : Color.gray)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(!canCreateRoute)
            }
        }
        .padding()
        .sheet(isPresented: $showingRouteMap) {
            NavigationView {
                VStack {
                    HStack {
                        Button("Done") {
                            showingRouteMap = false
                        }
                        .padding()
                        Spacer()
                    }

                    RouteMapView(selectedHouses: selectedHousesList)
                        .environmentObject(dataManager)
                }
                .navigationTitle("Route Preview")
                .navigationBarTitleDisplayMode(.inline)
                .navigationBarHidden(true)
            }
        }
        .alert("Route Created", isPresented: .constant(createdRoute != nil)) {
            Button("OK") {
                createdRoute = nil
            }
        } message: {
            if let route = createdRoute {
                Text("Route '\(route.name)' has been created with \(route.houseIds.count) houses.")
            }
        }
    }

    private var canCreateRoute: Bool {
        !routeName.isEmpty && selectedSalesperson != nil && selectedHousesList.count >= 2
    }

    private func statusColor(for status: HouseStatus) -> Color {
        switch status {
        case .new:
            return .green
        case .contacted:
            return .orange
        case .interested:
            return .blue
        case .notHome:
            return .yellow
        case .notInterested:
            return .red
        case .sold:
            return .purple
        }
    }

    private func createRoute() {
        guard canCreateRoute else { return }

        let route = Route(
            id: UUID(),
            name: routeName,
            salespersonId: selectedSalesperson!.id,
            houseIds: selectedHousesList.map { $0.id },
            createdAt: Date()
        )

        // Add route to data manager
        dataManager.addRoute(route)
        createdRoute = route

        // Reset form
        routeName = ""
        selectedSalesperson = nil
    }
}

struct RouteMapView: View {
    let selectedHouses: [House]
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 34.2257, longitude: -77.9447),
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )

    var body: some View {
        ZStack {
            Map(coordinateRegion: $region, annotationItems: selectedHouses) { house in
                MapAnnotation(coordinate: house.coordinate) {
                    VStack {
                        Image(systemName: "house.fill")
                            .foregroundColor(.white)
                            .font(.caption)
                            .frame(width: 30, height: 30)
                            .background(Color.blue)
                            .clipShape(Circle())

                        Text(house.address.components(separatedBy: ",").first ?? "")
                            .font(.caption2)
                            .padding(.horizontal, 4)
                            .padding(.vertical, 2)
                            .background(Color.white)
                            .foregroundColor(.black)
                            .cornerRadius(4)
                    }
                }
            }
            .ignoresSafeArea()

            // Route info overlay
            VStack {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Route Preview")
                            .font(.headline)
                            .foregroundColor(.white)

                        Text("\(selectedHouses.count) stops")
                            .font(.subheadline)
                            .foregroundColor(.white.opacity(0.8))
                    }

                    Spacer()
                }
                .padding()
                .background(Color.black.opacity(0.7))
                .cornerRadius(10)
                .padding()

                Spacer()
            }
        }
        .onAppear {
            centerMapOnHouses()
        }
    }

    private func centerMapOnHouses() {
        guard !selectedHouses.isEmpty else { return }

        let coordinates = selectedHouses.map { $0.coordinate }
        let minLat = coordinates.map { $0.latitude }.min() ?? 0
        let maxLat = coordinates.map { $0.latitude }.max() ?? 0
        let minLon = coordinates.map { $0.longitude }.min() ?? 0
        let maxLon = coordinates.map { $0.longitude }.max() ?? 0

        let centerLat = (minLat + maxLat) / 2
        let centerLon = (minLon + maxLon) / 2
        let latDelta = (maxLat - minLat) * 1.5
        let lonDelta = (maxLon - minLon) * 1.5

        region.center = CLLocationCoordinate2D(latitude: centerLat, longitude: centerLon)
        region.span = MKCoordinateSpan(
            latitudeDelta: max(latDelta, 0.01),
            longitudeDelta: max(lonDelta, 0.01)
        )
    }
}

extension View {
    func placeholder<Content: View>(
        when shouldShow: Bool,
        alignment: Alignment = .leading,
        @ViewBuilder placeholder: () -> Content) -> some View {

        ZStack(alignment: alignment) {
            placeholder().opacity(shouldShow ? 1 : 0)
            self
        }
    }
}

struct RouteCreationView_Previews: PreviewProvider {
    static var previews: some View {
        RouteCreationView(selectedHouses: Set(), allHouses: [])
            .environmentObject(DataManager())
    }
}
