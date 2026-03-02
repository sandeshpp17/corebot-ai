import Foundation

func chatCorebot(
    apiUrl: String,
    apiKey: String,
    message: String,
    mode: String = "auto",
    history: [[String: Any]] = [],
    appContext: [String: Any] = [:]
) async throws -> Data {
    let url = URL(string: "\(apiUrl)/chat/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    let payload: [String: Any] = [
        "message": message,
        "history": history,
        "mode": mode,
        "app_context": appContext
    ]
    request.httpBody = try JSONSerialization.data(withJSONObject: payload)
    let (data, response) = try await URLSession.shared.data(for: request)
    if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
        let body = String(data: data, encoding: .utf8) ?? ""
        throw NSError(
            domain: "Corebot",
            code: http.statusCode,
            userInfo: [NSLocalizedDescriptionKey: "Corebot request failed (\(http.statusCode)): \(body)"]
        )
    }
    return data
}
