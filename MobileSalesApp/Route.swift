import Foundation

struct Route: Identifiable, Codable {
    let id: UUID
    var name: String
    var salespersonId: UUID
    var houseIds: [UUID]
    var createdAt: Date
    
    init(id: UUID = UUID(), name: String, salespersonId: UUID, houseIds: [UUID] = [], 
         createdAt: Date = Date()) {
        self.id = id
        self.name = name
        self.salespersonId = salespersonId
        self.houseIds = houseIds
        self.createdAt = createdAt
    }
    
    var houseCount: Int {
        houseIds.count
    }
    
    var estimatedTime: String {
        // Rough estimate: 15 minutes per house + 5 minutes travel between houses
        let totalMinutes = houseIds.count * 15 + max(0, houseIds.count - 1) * 5
        let hours = totalMinutes / 60
        let minutes = totalMinutes % 60
        
        if hours > 0 {
            return "\(hours)h \(minutes)m"
        } else {
            return "\(minutes)m"
        }
    }
}
