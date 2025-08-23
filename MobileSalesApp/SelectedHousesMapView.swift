import SwiftUI
import MapKit

struct SelectedHousesMapView: View {
    let selectedHouses: Set<UUID>
    let allHouses: [House]
    @EnvironmentObject var dataManager: DataManager
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 34.2257, longitude: -77.9447),
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )
    @State private var selectedHouse: House?
    @State private var showingHouseDetail = false

    var selectedHousesList: [House] {
        allHouses.filter { selectedHouses.contains($0.id) }
    }

    var body: some View {
        ZStack {
            Map(coordinateRegion: $region, annotationItems: selectedHousesList) { house in
                MapAnnotation(coordinate: house.coordinate) {
                    HouseAnnotationView(house: house) {
                        selectedHouse = house
                        showingHouseDetail = true
                    }
                }
            }
            .ignoresSafeArea()

            VStack {
                Spacer()

                HStack {
                    Spacer()

                    VStack(spacing: 12) {
                        Button(action: {
                            // Center map on selected houses
                            centerMapOnSelectedHouses()
                        }) {
                            Image(systemName: "location.circle.fill")
                                .font(.title2)
                                .foregroundColor(.white)
                                .frame(width: 50, height: 50)
                                .background(Color.blue)
                                .clipShape(Circle())
                                .shadow(radius: 4)
                        }

                        Button(action: {
                            // Show route between selected houses
                            showRouteBetweenHouses()
                        }) {
                            Image(systemName: "arrow.triangle.turn.up.right.circle.fill")
                                .font(.title2)
                                .foregroundColor(.white)
                                .frame(width: 50, height: 50)
                                .background(Color.green)
                                .clipShape(Circle())
                                .shadow(radius: 4)
                        }
                    }
                    .padding(.trailing, 20)
                    .padding(.bottom, 100)
                }
            }

            // Info panel
            VStack {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Selected Houses")
                            .font(.headline)
                            .foregroundColor(.white)

                        Text("\(selectedHousesList.count) houses")
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
            centerMapOnSelectedHouses()
        }
        .sheet(isPresented: $showingHouseDetail) {
            if let house = selectedHouse {
                HouseDetailView(house: house)
                    .environmentObject(dataManager)
            }
        }
    }

    private func centerMapOnSelectedHouses() {
        guard !selectedHousesList.isEmpty else { return }

        if selectedHousesList.count == 1 {
            // Center on single house
            region.center = selectedHousesList[0].coordinate
            region.span = MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
        } else {
            // Calculate bounds for multiple houses
            let coordinates = selectedHousesList.map { $0.coordinate }
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

    private func showRouteBetweenHouses() {
        // This would integrate with Apple Maps or a routing service
        // For now, we'll just center the map
        centerMapOnSelectedHouses()
    }
}

struct SelectedHousesMapView_Previews: PreviewProvider {
    static var previews: some View {
        SelectedHousesMapView(selectedHouses: Set(), allHouses: [])
            .environmentObject(DataManager())
    }
}
