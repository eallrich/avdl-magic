(function () {

  'use strict';

  angular.module('ytdlApp', [])

  .controller('ytdlController', ['$scope', '$log', '$http', function($scope, $log, $http) {
    $scope.watchQueue = function() {
      $log.log('watchQueue called')
    };
  }

  ]);

}());
