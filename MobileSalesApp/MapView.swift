import SwiftUI
import MapKit
import CoreLocation

struct MapView: View {
    @EnvironmentObject var dataManager: DataManager
    @StateObject private var locationManager = LocationManager()
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 34.2257, longitude: -77.9447),
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )
    @State private var selectedHouse: House?
    @State private var showingHouseDetail = false
    @State private var showingRouteToHouse = false

    var body: some View {
        NavigationView {
            ZStack {
                Map(coordinateRegion: $region, annotationItems: dataManager.houses) { house in
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
                                // Refresh data
                                dataManager.importFromBigBeautifulProgram()
                            }) {
                                Image(systemName: "arrow.clockwise")
                                    .font(.title2)
                                    .foregroundColor(.white)
                                    .frame(width: 50, height: 50)
                                    .background(Color.blue)
                                    .clipShape(Circle())
                                    .shadow(radius: 4)
                            }

                            Button(action: {
                                // Center on user location
                                if let userLocation = locationManager.userLocation {
                                    region.center = userLocation.coordinate
                                }
                            }) {
                                Image(systemName: "location.fill")
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
            }
            .navigationTitle("Sales Map")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showingHouseDetail) {
                if let house = selectedHouse {
                    HouseDetailView(house: house)
                        .environmentObject(dataManager)
                }
            }
        }
    }
}

struct HouseAnnotationView: View {
    let house: House
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            ZStack {
                Circle()
                    .fill(statusColor)
                    .frame(width: 30, height: 30)
                    .shadow(radius: 2)

                Image(systemName: "house.fill")
                    .foregroundColor(.white)
                    .font(.caption)

                if house.adtSignDetected {
                    Image(systemName: "exclamationmark.triangle")
                        .foregroundColor(.red)
                        .font(.system(size: 12))
                        .offset(x: 10, y: -10)
                }
            }
        }
    }

    private var statusColor: Color {
        switch house.status {
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
}

struct IncidentAnnotationView: View {
    let incident: Incident

    var body: some View {
        ZStack {
            Circle()
                .fill(Color.red)
                .frame(width: 35, height: 35)
                .shadow(radius: 2)

            Image(systemName: incident.iconName)
                .foregroundColor(.white)
                .font(.caption)
        }
    }
}

struct MapView_Previews: PreviewProvider {
    static var previews: some View {
        MapView()
            .environmentObject(DataManager())
    }
}

// MARK: - Location Manager

class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let locationManager = CLLocationManager()
    @Published var userLocation: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined

    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
        locationManager.distanceFilter = 10
    }

    func requestLocationPermission() {
        locationManager.requestWhenInUseAuthorization()
    }

    func startUpdatingLocation() {
        locationManager.startUpdatingLocation()
    }

    // MARK: - CLLocationManagerDelegate

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        userLocation = location
    }

    func locationManager(_ manager: CLLocationManager, didChangeAuthorization status: CLAuthorizationStatus) {
        authorizationStatus = status

        if status == .authorizedWhenInUse || status == .authorizedAlways {
            startUpdatingLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("Location manager failed with error: \(error)")
    }
}
