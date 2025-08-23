import Foundation
import CoreLocation

struct Incident: Identifiable, Codable {
    let id: UUID
    var address: String
    var incidentType: IncidentType
    var description: String
    var latitude: Double
    var longitude: Double
    var assignedSalespersonId: UUID?
    var status: IncidentStatus
    var createdAt: Date
    
    init(id: UUID = UUID(), address: String, incidentType: IncidentType, description: String,
         latitude: Double, longitude: Double, assignedSalespersonId: UUID? = nil,
         status: IncidentStatus = .active, createdAt: Date = Date()) {
        self.id = id
        self.address = address
        self.incidentType = incidentType
        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.assignedSalespersonId = assignedSalespersonId
        self.status = status
        self.createdAt = createdAt
    }
    
    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
    
    var iconName: String {
        switch incidentType {
        case .fire:
            return "flame.fill"
        case .breakIn:
            return "lock.break"
        case .flood:
            return "drop.fill"
        case .storm:
            return "cloud.bolt.fill"
        case .theft:
            return "hand.raised.fill"
        }
    }
    
    var color: String {
        switch incidentType {
        case .fire:
            return "red"
        case .breakIn:
            return "orange"
        case .flood:
            return "blue"
        case .storm:
            return "purple"
        case .theft:
            return "yellow"
        }
    }
}

enum IncidentType: String, CaseIterable, Codable {
    case fire = "fire"
    case breakIn = "break-in"
    case flood = "flood"
    case storm = "storm"
    case theft = "theft"
    
    var displayName: String {
        switch self {
        case .fire:
            return "Fire"
        case .breakIn:
            return "Break-in"
        case .flood:
            return "Flood"
        case .storm:
            return "Storm"
        case .theft:
            return "Theft"
        }
    }
}

enum IncidentStatus: String, CaseIterable, Codable {
    case active = "active"
    case responded = "responded"
    case resolved = "resolved"
    
    var displayName: String {
        switch self {
        case .active:
            return "Active"
        case .responded:
            return "Responded"
        case .resolved:
            return "Resolved"
        }
    }
}
