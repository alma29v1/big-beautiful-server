import Foundation

struct Visit: Identifiable, Codable {
    let id: UUID
    var houseId: UUID
    var salespersonId: UUID
    var visitDate: Date
    var status: VisitStatus
    var notes: String
    var followUpDate: Date?
    var createdAt: Date
    
    init(id: UUID = UUID(), houseId: UUID, salespersonId: UUID, visitDate: Date = Date(),
         status: VisitStatus, notes: String = "", followUpDate: Date? = nil, 
         createdAt: Date = Date()) {
        self.id = id
        self.houseId = houseId
        self.salespersonId = salespersonId
        self.visitDate = visitDate
        self.status = status
        self.notes = notes
        self.followUpDate = followUpDate
        self.createdAt = createdAt
    }
    
    var formattedVisitDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: visitDate)
    }
    
    var formattedFollowUpDate: String? {
        guard let followUpDate = followUpDate else { return nil }
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter.string(from: followUpDate)
    }
}

enum VisitStatus: String, CaseIterable, Codable {
    case contacted = "contacted"
    case interested = "interested"
    case notInterested = "not-interested"
    case followUp = "follow-up"
    
    var displayName: String {
        switch self {
        case .contacted:
            return "Contacted"
        case .interested:
            return "Interested"
        case .notInterested:
            return "Not Interested"
        case .followUp:
            return "Follow Up"
        }
    }
    
    var color: String {
        switch self {
        case .contacted:
            return "orange"
        case .interested:
            return "green"
        case .notInterested:
            return "red"
        case .followUp:
            return "blue"
        }
    }
}
