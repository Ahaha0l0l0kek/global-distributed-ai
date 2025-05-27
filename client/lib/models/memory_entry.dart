class MemoryEntry {
  final DateTime timestamp;
  final String observation;
  final String plan;
  final String result;

  MemoryEntry({
    required this.timestamp,
    required this.observation,
    required this.plan,
    required this.result,
  });

  factory MemoryEntry.fromJson(Map<String, dynamic> json) {
    return MemoryEntry(
      timestamp: DateTime.parse(json['timestamp']),
      observation: json['observation'],
      plan: json['plan'],
      result: json['result'],
    );
  }
}