import 'package:dio/dio.dart';
import '../models/memory_entry.dart';

class ApiService {
  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: "http://10.0.2.2:8000", // для Android эмулятора (localhost)
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 10),
    ),
  );

  /// Получает список последних записей памяти агента
  Future<List<MemoryEntry>> getMemory() async {
    try {
      final response = await _dio.get("/memory");
      final data = response.data as List;
      return data.map((e) => MemoryEntry.fromJson(e)).toList();
    } catch (e) {
      print("❌ Ошибка при получении памяти: $e");
      return [];
    }
  }

  /// Отправляет URL на анализ агенту
  Future<MemoryEntry?> observeUrl(String url) async {
    try {
      final response = await _dio.post("/observe", data: {
        "url": url,
      });
      return MemoryEntry.fromJson(response.data);
    } catch (e) {
      print("❌ Ошибка при отправке URL: $e");
      return null;
    }
  }
}