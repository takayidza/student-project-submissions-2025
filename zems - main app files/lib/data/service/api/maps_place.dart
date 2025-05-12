import 'package:dio/dio.dart';
import 'package:zems/utils/constant/api_url.dart';
import 'dart:developer';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../model/find_hospital_place_info.dart';

class PlacesWebservices {
  static Dio dio = Dio();

  // static Future<void> fetchNearestHospitals(
  //     double latitude, double longitude) async {
  //   final Map<String, dynamic> queryParameters = {
  //     'location': '$latitude,$longitude',
  //     'radius': '5000',
  //     'type': 'hospital',
  //     'key': ApiUrlManager.googleMap,
  //   };

  //   try {
  //     final response =
  //         await _dio.get(, queryParameters: queryParameters);
  //     if (response.statusCode == 200) {
  //       print('Hospitals data: ${response.data}');
  //       // Handle the received data
  //     } else {
  //       print('Error fetching hospitals: ${response.statusMessage}');
  //     }
  //   } catch (e) {
  //     print('Exception caught: $e');
  //   }
  // }

  //! Fetch Suggetions.
  static Future fetchPlaceSuggestions(String place, String sessionToken,
      {double? latitude, double? longitude}) async {
    try {
      if (place.trim().isEmpty) {
        return [];
      }

      Response response = await dio.get(
        ApiUrlManager.placeSuggetion,
        queryParameters: {
          'location': '$latitude,$longitude',
          'radius': 50000,
          'input': place,
          'region': 'zw',
          'components': 'country:zw',
          'types': 'hospital|doctor|clinic|pharmacy',
          'key': ApiUrlManager.googleMapApiKey,
          'sessiontoken': sessionToken,
        },
      );

      if (response.statusCode != 200) {
        throw DioException(
          requestOptions: response.requestOptions,
          response: response,
          error: 'Failed to fetch place suggestions',
        );
      }

      if (response.data == null || response.data['predictions'] == null) {
        return [];
      }

      return response.data['predictions'];
    } on DioException catch (e) {
      log('Dio error in fetchPlaceSuggestions: ${e.message}');
      rethrow;
    } catch (err) {
      log('Error in fetchPlaceSuggestions: $err');
      rethrow;
    }
  }

  //! fetch Location
  static Future fetchPlaceLocation(String placeId, String sessionToken) async {
    try {
      Response response = await dio.get(
        ApiUrlManager.placeLocation,
        queryParameters: {
          'place_id': placeId,
          'fields': 'geometry',
          'key': ApiUrlManager.googleMapApiKey,
          'sessiontoken': sessionToken,
        },
      );
      return response.data;
    } on DioException {
      return Future.error(
          "Place location error: ", StackTrace.fromString("this is the trace"));
    } catch (err) {
      log('Dio Method err:$err');
    }
  }

  //! get destination
  static Future getPlaceDirections(LatLng origin, LatLng destination) async {
    try {
      Response response = await dio.get(
        ApiUrlManager.directions,
        queryParameters: {
          'origin': '${origin.latitude},${origin.longitude}',
          'destination': '${destination.latitude},${destination.longitude}',
          'key': ApiUrlManager.googleMapApiKey,
        },
      );
      return response.data;
    } on DioException {
      return Future.error("Place destination error: ",
          StackTrace.fromString("this is the trace"));
    } catch (err) {
      log('Dio Method err:$err');
    }
  }

  static Future getNearestHospital(
      double latitude, double longitude, String sessionToken) async {
    final queryParameters = {
      'location': '$latitude,$longitude',
      'radius': '5000',
      'types': 'hospital',
      'key': ApiUrlManager.googleMapApiKey,
      'sessiontoken': sessionToken,
    };

    try {
      final response = await dio.get(ApiUrlManager.nearestHospital,
          queryParameters: queryParameters);
      // log("Nearby hospitals data are here: ${response.data}");

      for (int i = 0; i < response.data['results'].length; i++) {
        log(response.data['results'][i]['name']);
      }
    } catch (err) {
      log(err.toString());
    }
  }
}

class FindHospitalWebService {
  static final Dio dio = Dio();

  static Future<List<FindHospitalsPlaceInfo>> getNearestHospital(
      double latitude, double longitude, double? radius) async {
    List<FindHospitalsPlaceInfo> hospitals = [];

    log('Searching for nearest hospitals...');
    try {
      final response = await dio.get(
        ApiUrlManager.nearestHospital,
        queryParameters: {
          'location': '$latitude,$longitude',
          'radius': radius?.toString() ?? '50000',
          'types': 'hospital|doctor|clinic|pharmacy',
          'components': 'country:zw',
          'key': ApiUrlManager.googleMapApiKey,
        },
      );

      if (response.statusCode != 200) {
        throw DioException(
          requestOptions: response.requestOptions,
          response: response,
          error: 'Failed to fetch nearby hospitals',
        );
      }

      if (response.data == null || response.data['results'] == null) {
        log('No results found');
        return hospitals;
      }

      final List<dynamic> results = response.data['results'];
      log('Found ${results.length} facilities');
      
      for (var item in results) {
        try {
          hospitals.add(FindHospitalsPlaceInfo.fromJson(item));
        } catch (e) {
          log('Error parsing hospital data: $e');
        }
      }
    } on DioException catch (e) {
      log('Dio error in getNearestHospital: ${e.message}');
      rethrow;
    } catch (err) {
      log('Error in getNearestHospital: $err');
      rethrow;
    }

    return hospitals;
  }
}
