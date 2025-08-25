import Foundation
import CoreLocation

struct House: Identifiable, Codable {
    let id: UUID
    let address: String
    let city: String
    let state: String
    let zipCode: String
    let latitude: Double
    let longitude: Double
    let soldDate: String
    let price: Double
    let contactName: String
    let contactEmail: String
    let contactPhone: String
    let fiberAvailable: Bool
    let adtDetected: Bool
    let adtSignDetected: Bool // Corrected property for ADT sign detection
    var status: HouseStatus = .new
    var notes: String = ""

    // Update CodingKeys to include notes
    enum CodingKeys: String, CodingKey {
        case id, address, city, state, latitude, longitude, price, status, notes
        case zipCode = "zip_code"
        case soldDate = "sold_date"
        case contactName = "contact_name"
        case contactEmail = "contact_email"
        case contactPhone = "contact_phone"
        case fiberAvailable = "fiber_available"
        case adtDetected = "adt_detected"
        case adtSignDetected = "adt_sign_detected"
    }

    // Update init if needed
    init(address: String, city: String, state: String, zipCode: String, latitude: Double, longitude: Double, soldDate: String, price: Double, contactName: String, contactEmail: String, contactPhone: String, fiberAvailable: Bool, adtDetected: Bool, adtSignDetected: Bool = false) {
        self.id = UUID()
        self.address = address
        self.city = city
        self.state = state
        self.zipCode = zipCode
        self.latitude = latitude
        self.longitude = longitude
        self.soldDate = soldDate
        self.price = price
        self.contactName = contactName
        self.contactEmail = contactEmail
        self.contactPhone = contactPhone
        self.fiberAvailable = fiberAvailable
        self.adtDetected = adtDetected
        self.adtSignDetected = adtSignDetected
        self.status = .new
        self.notes = ""
    }

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    var fullAddress: String {
        "\(address), \(city), \(state) \(zipCode)"
    }

    var formattedPrice: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: price)) ?? "$\(price)"
    }

    var statusColor: String {
        switch status {
        case .new:
            return "green"
        case .contacted:
            return "orange"
        case .interested:
            return "blue"
        case .notHome:
            return "yellow"
        case .notInterested:
            return "red"
        case .sold:
            return "purple"
        }
    }
}

enum HouseStatus: String, CaseIterable, Codable {
    case new = "new"
    case contacted = "contacted"
    case interested = "interested"
    case notHome = "notHome"
    case notInterested = "notInterested"
    case sold = "sold"

    var displayName: String {
        switch self {
        case .new:
            return "New"
        case .contacted:
            return "Contacted"
        case .interested:
            return "Interested"
        case .notHome:
            return "Not Home"
        case .notInterested:
            return "Not Interested"
        case .sold:
            return "Sold"
        }
    }

    var color: String {
        switch self {
        case .new:
            return "green"
        case .contacted:
            return "orange"
        case .interested:
            return "blue"
        case .notHome:
            return "yellow"
        case .notInterested:
            return "red"
        case .sold:
            return "purple"
        }
    }
}
