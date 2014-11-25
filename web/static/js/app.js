'use strict';


// Declare app level module which depends on filters, and services
angular.module('myApp', [
  'ngRoute'
])
.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/home', {templateUrl: '/home.html', controller: 'homeController'});
    $routeProvider.otherwise({redirectTo: '/home'});
}])
.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
})
.directive('tooltip', function(){
    return {
        restrict: 'A',
        link: function(scope, element, attrs){
            if(attrs.title != null){                   
                $(element).hover(function(){
                    // on mouseenter
                    $(element).tooltip({
                        'placement': 'bottom'
                    });
                    $(element).tooltip('show');
                }, function(){
                    // on mouseleave
                    $(element).tooltip('hide');
                });

            }
        }
    };
})
.controller('homeController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
            $http.post('jobs', $scope.page_request).success(function(data, status, headers, config){
                $scope.paged_result = data;
                $scope.jobs=data.content;
            }).error(function(data, status, headers, config){

            });
        }

        $scope.refresh = function(){
            $scope.fetchData();
        }

        $scope.page_request = {
            'page_no': 1,
            'size': 25,
        }

        $scope.page_size_options = [25, 50, 100]

        $scope.paginationListener = function(newVal, oldValue){
            $scope.fetchData();
        }

        $scope.toPreviousPage = function(){
            if($scope.page_request.page_no > 1){
                $scope.page_request.page_no = $scope.page_request.page_no - 1;   
            }
        }

        $scope.toNextPage = function(){
            if($scope.page_request.page_no < $scope.paged_result.total_pages){
                $scope.page_request.page_no = $scope.page_request.page_no + 1;       
            }
            
        }

        //setup the watch function for the pagination
        $scope.$watch('page_request', $scope.paginationListener, true)
 }]);