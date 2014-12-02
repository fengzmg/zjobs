'use strict';


// Declare app level module which depends on filters, and services
angular.module('myApp', [
  'ngRoute', 'ngSanitize'
])
.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/home', {templateUrl: '/home.html', controller: 'homeController'});
    $routeProvider.otherwise({redirectTo: '/home'});
}])
.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
})
.config(function($httpProvider) {
    $httpProvider.interceptors.push(function($q, $rootScope, $timeout) {
        return {
            'request': function(config) {
                $timeout(function(){
                    $rootScope.$broadcast('loading:started', '');
                }, 30);
                
                return config || $q.when(config);
            },
            'response': function(response) {

                $timeout(function(){
                    $rootScope.$broadcast('loading:completed', '');
                },  30);
                
                return response || $q.when(response);
            }
        };
    });
})
.filter('displayAsIcon', ['$sce',function($sce) {
    var site_urls = {
    'sgxin':'http://www.sgxin.com',
    'shichengbbs':'http://www.shichengbbs.com'
    }
  return function(source) {
    return $sce.trustAsHtml('<a href="'+ site_urls[source] +'" target="_blank"><img class="siteImage"  src="/static/image/'+source+'_logo.png"/></a>');
  };
}])
.filter('siteImageUrl', function() {
  return function(source) {
    return '/static/image/'+source+'_logo.png';
  };
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
.directive("loadingindicator", function($rootScope) {
    return {
        replace: true,
        controller : function($rootScope) {
            $rootScope.$on("loading:started", function(e, data) {   
                $("#loader").show();
            });

            $rootScope.$on("loading:completed", function(e, data) {
                $("#loader").hide();
            });

        },

        template: '<img id="loader" src="/static/image/ajax-loader.gif" style="display: none"/>'
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