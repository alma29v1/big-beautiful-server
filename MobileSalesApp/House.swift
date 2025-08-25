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
    var status: HouseStatus = .new
    let ownerName: String
    let ownerEmail: String
    let ownerPhone: String
    let soldDate: String
    let price: Int?
    let squareFootage: Int?
    let bedrooms: Int?
    let bathrooms: Int?
    let adtSignDetected: Bool
    var notes: String = ""

    enum CodingKeys: String, CodingKey {
        case id, address, city, state, latitude, longitude, status, price, bedrooms, bathrooms, notes
        case zipCode = "zip_code"
        case ownerName = "owner_name"
        case ownerEmail = "owner_email"
        case ownerPhone = "owner_phone"
        case soldDate = "sold_date"
        case squareFootage = "square_footage"
        case adtSignDetected = "adt_sign_detected"
    }

    init(id: UUID = UUID(), address: String, city: String, state: String, zipCode: String, latitude: Double, longitude: Double, status: HouseStatus = .new, ownerName: String, ownerEmail: String, ownerPhone: String, soldDate: String, price: Int? = nil, squareFootage: Int? = nil, bedrooms: Int? = nil, bathrooms: Int? = nil, adtSignDetected: Bool = false, notes: String = "") {
        self.id = id
        self.address = address
        self.city = city
        self.state = state
        self.zipCode = zipCode
        self.latitude = latitude
        self.longitude = longitude
        self.status = status
        self.ownerName = ownerName
        self.ownerEmail = ownerEmail
        self.ownerPhone = ownerPhone
        self.soldDate = soldDate
        self.price = price
        self.squareFootage = squareFootage
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.adtSignDetected = adtSignDetected
        self.notes = notes
    }

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    var fullAddress: String {
        "\(address), \(city), \(state) \(zipCode)"
    }

    var formattedPrice: String {
        guard let price = price else { return "N/A" }
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
