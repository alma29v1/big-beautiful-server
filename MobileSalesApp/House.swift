import Foundation
import CoreLocation

struct House: Identifiable, Codable {
    let id: UUID
    var address: String
    var city: String
    var state: String
    var zipCode: String
    var latitude: Double
    var longitude: Double
    var soldDate: String
    var price: Double
    var contactName: String
    var contactEmail: String
    var contactPhone: String
    var fiberAvailable: Bool
    var adtDetected: Bool
    var status: HouseStatus
    var notes: String
    var createdAt: Date
    
    init(id: UUID = UUID(), address: String, city: String, state: String, zipCode: String, 
         latitude: Double, longitude: Double, soldDate: String, price: Double, 
         contactName: String, contactEmail: String, contactPhone: String, 
         fiberAvailable: Bool, adtDetected: Bool, status: HouseStatus = .new, 
         notes: String = "", createdAt: Date = Date()) {
        self.id = id
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
        self.status = status
        self.notes = notes
        self.createdAt = createdAt
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
