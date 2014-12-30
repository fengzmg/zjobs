'use strict';


// Declare app level module which depends on filters, and services
angular.module('myApp', [
  'ngRoute', 'ngSanitize'
])
.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/jobs', {templateUrl: '/html/jobs', controller: 'jobsController'});
    $routeProvider.when('/reject_rules', {templateUrl: '/protected/html/reject_rules', controller: 'reject_rulesController'});
    $routeProvider.when('/blocked_contacts', {templateUrl: '/protected/html/blocked_contacts', controller: 'blocked_contactsController'});
    $routeProvider.when('/configs', {templateUrl: '/protected/html/configs', controller: 'configsController'});
    $routeProvider.when('/users', {templateUrl: '/protected/html/users', controller: 'usersController'});
    $routeProvider.otherwise({redirectTo: '/jobs'});
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
    'shichengbbs':'http://www.shichengbbs.com',
    'singxin':'http://www.singxin.com',
    'sggongzuo': 'http://www.gongzuo.sg'
    }
  return function(source) {
    return $sce.trustAsHtml('<a href="'+ site_urls[source] +'" target="_blank"><img class="siteImage"  src="/static/image/'+source+'_logo.png"/></a>');
  };
}])
.filter('displayAsPhoneLink', ['$sce',function($sce) {
  return function(source) {
    if(source && source !=''){
        return $sce.trustAsHtml('<span class="glyphicon glyphicon-phone-alt">&nbsp;</span><a href="tel:'+ source +'" target="_blank">'+source+'</a>');
    }else{
        return $sce.trustAsHtml('');   
    }
    
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
.directive("loadingIndicator", ['$rootScope', function($rootScope) {
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
}])
.directive("menu", ['$http', function($http) {
    return {
        replace: true,
        controller : function($scope) {
            $scope.menu_item_classes={
                'admin_run_crawler':'glyphicon glyphicon-repeat',
                'admin_run_housekeeper':'glyphicon glyphicon-paperclip',
                'admin_run_emailer':'glyphicon glyphicon-envelope',
                'admin_config_reject_rules': 'glyphicon glyphicon-cog',
                'admin_config_blocked_contacts': 'glyphicon glyphicon-wrench',
                'admin_config_app_settings': 'glyphicon glyphicon-asterisk',
                'admin_config_users': 'glyphicon glyphicon-user',
                'extract_jobs_xlsx':'glyphicon glyphicon-floppy-disk'
            }

            $http.get('/menus').success(
                function(data, status, headers, config){
                    $scope.menu_items = data.menu_items;
                }
                ).error(
                    function(data, status, headers, config){
                        alert('Cannot load menu');
                    }                   
                );

        },

        template: '<div class="dropdown" style="display:inline-block">' +
          '<a class="dropdown-toggle" id="adminMenu" data-toggle="dropdown">' + 
            'menu' +
            '&nbsp;<span class="glyphicon glyphicon-tasks"></span>' +
          '</a>' +
          '<ul class="dropdown-menu dropdown-menu-right" role="menu" aria-labelledby="adminMenu">' +
            '<li role="presentation" ng-repeat="menu_item in menu_items">' +
                '<a role="menuitem" tabindex="-1" href="[[ menu_item.link]]"><span class="[[ menu_item_classes[menu_item.menu_item_id] ]]"></span>&nbsp;[[menu_item.label]]</a>'+
            '</li>' +
          '</ul>' +
        '</div>'

    };
}])
.directive("userLogin", function($http){
    return {
        link: function(scope, element, attrs){

            var login_modalBox = '<div id="target_login_modal" class="modal">' +
                                      '<div class="modal-dialog" style="width:350px;">' +
                                        '<div class="modal-content">' +
                                          '<div class="modal-header">' +
                                            '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
                                            '<h4 class="modal-title">Login</h4>' +
                                          '</div>' +

                                          '<form action="/login" method="post">' +
                                          '<div class="modal-body">' +
                                            '<div style="margin-bottom: 5px;">' +
                                                '<label style="width:30%;display:inline-block;">User Name:</label><input id="username" name="username" type="text" class="form-control" style="width:70%;display:inline-block;"/>' +
                                            '</div>' +
                                            '<div style="margin-bottom: 5px;">' +
                                                '<label style="width:30%;display:inline-block;">Password:</label><input id="password" name="password" type="password" value="" class="form-control" style="width:70%;display:inline-block;"/>' +
                                            '</div>' +
                                            '<div style="margin-bottom: 5px;">' +
                                                '<div style="width:50%; display:inline-block"><a href="#" id="register_user_link">Register New User</a></div><div style="width:50%;display:inline-block"><a href="">Forgot Password</a></div>' +
                                            '</div>' +
                                          '</div>' +
                                          '<div class="modal-footer">' +
                                            '<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>' +
                                            '<button type="submit" class="btn btn-success" id="confirm_login">Login</button>' +
                                          '</div>' +
                                          '</form>' +
                                        '</div><!-- /.modal-content -->' +
                                      '</div><!-- /.modal-dialog -->' +
                                    '</div><!-- /.modal -->';

             var register_modalBox = '<div id="target_register_modal" class="modal">' +
                                      '<div class="modal-dialog" style="width:350px;">' +
                                        '<div class="modal-content">' +
                                          '<div class="modal-header">' +
                                            '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
                                            '<h4 class="modal-title">Create User</h4>' +
                                          '</div>' +

                                          '<form action="/users/register" method="post">' +
                                          '<div class="modal-body">' +
                                            '<div style="margin-bottom: 5px;">' +
                                                '<label style="width:30%;display:inline-block;">User Name:</label><input id="username" name="username" type="text" class="form-control" style="width:70%;display:inline-block;"/>' +
                                            '</div>' +
                                            '<div style="margin-bottom: 5px;">' +
                                                '<label style="width:30%;display:inline-block;">Password:</label><input id="password" name="password" type="password" value="" class="form-control" style="width:70%;display:inline-block;"/>' +
                                            '</div>' +
                                            '<div style="margin-bottom: 5px;">' +
                                                '<label style="width:30%;display:inline-block;">Email:</label><input id="email" name="email" type="text" value="" class="form-control" style="width:70%;display:inline-block;"/>' +
                                            '</div>' +

                                          '</div>' +
                                          '<div class="modal-footer">' +
                                            '<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>' +
                                            '<button type="submit" class="btn btn-success" id="confirm_register">Register</button>' +
                                          '</div>' +
                                          '</form>' +
                                        '</div><!-- /.modal-content -->' +
                                      '</div><!-- /.modal-dialog -->' +
                                    '</div><!-- /.modal -->';

            var target_login_modal = jQuery(login_modalBox).modal({
                'backdrop': 'static',
                'show': false
            });

            var target_register_modal = jQuery(register_modalBox).modal({
                'backdrop': 'static',
                'show': false
            });

            jQuery('#register_user_link', target_login_modal).click(function(e){
                e.preventDefault();
                e.stopPropagation();
                target_login_modal.modal('hide');
                target_register_modal.modal('show');
            });

            jQuery(element).click(function(e){
                e.preventDefault();
                e.stopPropagation();
                target_login_modal.modal('show');
            });
        }
    };
})
.directive("rightclick", ['$parse', function($parse, $scope) {
    return {
        restrict: 'A',
        transclude: true,
        scope:{
            'rightclick': '&rightclick'
        },
        link: function(scope, element, attrs) {

                element.bind('contextmenu', function(event) {
                    var fn = $parse(scope.rightclick); //parse it as function
                    scope.$apply(function() {
                        event.stopPropagation();
                        event.preventDefault();
                        fn();
                    });
                });
        }

    };
}])
.directive("contactContextMenu", function($parse, $timeout, $http) {
    return {
        restrict: 'A',
        scope: true,
        link: function(scope, element, attrs) {

            //give some time for angular to render the html
            $timeout(function(){
                var contact = jQuery('a', element).text();

                var template='<div class="dropdown">' +
                      '<div class="dropdown-toggle" id="dropdownContextMenu" data-toggle="dropdown" aria-expanded="true">' + 
                        element.html() +
                      '</div>' +
                      '<ul class="dropdown-menu dropdown-menu-right" role="menu" aria-labelledby="dropdownContextMenu">' +
                        '<li role="presentation">' +
                            '<a role="menuitem" tabindex="-1" class="context-menu-item_block_contact" href="#"><span class="glyphicon glyphicon-warning-sign">&nbsp;</span>Block Contact</a>'+
                            '<a role="menuitem" tabindex="-1" href="tel:'+ contact + '"><span class="glyphicon glyphicon-earphone">&nbsp;</span>Call Contact</a>'+
                        '</li>' +
                      '</ul>' +
                    '</div>';

                    var modalBox = '<div id="block_contact_modal" class="modal">' +
                                      '<div class="modal-dialog modal-sm">' +
                                        '<div class="modal-content">' +
                                          '<div class="modal-header">' +
                                            '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
                                            '<h4 class="modal-title">Please Enter Block Reason</h4>' +
                                          '</div>' +
                                          '<div class="modal-body">' +
                                            '<input id="block_reason" type="text" class="form-control"/>' +
                                          '</div>' +
                                          '<div class="modal-footer">' +
                                            '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>' +
                                            '<button type="button" class="btn btn-primary" id="confirm_block" >Block</button>' +
                                          '</div>' +
                                        '</div><!-- /.modal-content -->' +
                                      '</div><!-- /.modal-dialog -->' +
                                    '</div><!-- /.modal -->';

                jQuery(element).html(template + modalBox);

                var block_contact_modal = jQuery('#block_contact_modal', element).modal({
                            'backdrop':'static',
                            'show': false
                        });

                jQuery('a.context-menu-item_block_contact', element).click(function(e){
                    scope.$apply(function(){
                        e.stopPropagation();
                        e.preventDefault();

                        block_contact_modal.modal('show');

                        jQuery('#confirm_block', element).click(function(){
                            block_contact_modal.modal('hide');
                            var block_reason = jQuery('#block_reason', block_contact_modal).val();

                            scope.markAsBlockedContact({'contact': contact, 'block_reason': block_reason});

                        });

                    });
                });
            }, 100);

            jQuery(element).click(function(e){
                jQuery('.dropdown-toggle', element).removeAttr('data-toggle');
            });

            element.bind('contextmenu', function(event) {
                
                scope.$apply(function() {
                    event.stopPropagation();
                    event.preventDefault();
                    jQuery('.dropdown-toggle', element).attr('data-toggle', 'dropdown');
                    jQuery('.dropdown-toggle', element).dropdown('toggle');
                });
            });
            
        }

    };
})
.directive('jobContextMenu', function($http, $timeout){
    return{
        restrict: 'A',
        scope: true,
        link: function(scope, element, attrs) {

            element.bind('contextmenu', function(e){
                jQuery('.dropdown-toggle', element).attr('data-toggle', 'dropdown');
                jQuery('.dropdown-toggle', element).dropdown('toggle');
                return false;
            });

           jQuery(element).click(function(e){
                jQuery('.dropdown-toggle', element).removeAttr('data-toggle');
            });

            $timeout(function(){

                var job_title = jQuery('a', element).text();
                var template='<div class="dropdown">' +
                      '<div class="dropdown-toggle" id="dropdownContextMenu"  aria-expanded="true">' +
                        element.html() +
                      '</div>' +
                      '<ul class="dropdown-menu dropdown-menu-right" role="menu" aria-labelledby="dropdownContextMenu">' +
                        '<li role="presentation">' +
                            '<a role="menuitem" tabindex="-1" class="context-menu-item_remove_job" href="#"><span class="glyphicon glyphicon-trash">&nbsp;</span>Remove Job</a>'+

                        '</li>' +
                      '</ul>' +
                    '</div>';

                jQuery(element).html(template);

                jQuery('a.context-menu-item_remove_job', element).click(function(e){
                    scope.$apply(function(){
                        e.stopPropagation();
                        e.preventDefault();
                        scope.remove({'job_title': job_title });
                    });
                });

            }, 100);
        }
    }
})
.directive('fileUpload', function(){
    return{
        restrict: 'A',
        scope: true,
        link: function(scope, element, attrs){
            var upload_url = attrs.fileUpload;
            var redirect_url = attrs.fileUploadRedirectUrl;

            var modalBox = '<div id="target_modal" class="modal">' +
                                      '<div class="modal-dialog modal-sm">' +
                                        '<div class="modal-content">' +
                                          '<div class="modal-header">' +
                                            '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
                                            '<h4 class="modal-title">Please specify the file to import</h4>' +
                                          '</div>' +
                                          '<form id="upload_form" action="'+ upload_url +'" method="post" enctype="multipart/form-data">' +
                                          '<div class="modal-body">' +
                                            '<input id="file_to_upload" name="file_to_upload" type="file" class="form-control"/>' +
                                            '<input id="redirect_url" name="redirect_url" type="hidden" value="'+ redirect_url +'"/>' +
                                            '<img id="loader" src="/static/image/ajax-loader.gif" style="display: none;"/>' +
                                          '</div>' +
                                          '<div class="modal-footer">' +
                                            '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>' +
                                            '<button type="button" class="btn btn-primary" id="confirm_upload">Import</button>' +
                                          '</div>' +
                                          '</form>' +
                                        '</div><!-- /.modal-content -->' +
                                      '</div><!-- /.modal-dialog -->' +
                                    '</div><!-- /.modal -->';

            var target_modal = jQuery(modalBox).modal({
                'backdrop': 'static',
                'show': false
            });

            element.click(function(e){
                target_modal.modal('show');
                jQuery('#confirm_upload', target_modal).click(function(e){
                    jQuery('#loader', target_modal).show();
                    jQuery('form#upload_form', target_modal).submit();
                });
            });
        }
    };
})
.controller('reject_rulesController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
        $http.post('/reject_rules', $scope.page_request).success(function(data, status, headers, config){
            $scope.paged_result = data;
            $scope.records=$scope.paged_result.content;
        }).error(function(data, status, headers, config){
            alert('Unable to load records');
        });
    }

    $scope.add_new = function(){
        $scope.records.push({'reject_pattern': '', 'reject_reason': '', 'is_new': true});
    }

    $scope.save = function(record){
        $http.post('/reject_rules/save', record).success(function(data, status, headers, config){
            record.is_new = false;
            record.is_modify = false;
        }).error(function(data, status, headers, config){
            alert('Cannot save record');
        });
    }

    $scope.remove = function(index){
        var record = $scope.records[index];
        $http.post('/reject_rules/remove', record).success(function(data, status, headers, config){
            $scope.records.splice(index, 1);
        }).error(function(data, status, headers, config){
            alert('Cannot remove record');
        });


    }

    $scope.modify = function(index){
        var record = $scope.records[index];
        record.is_modify = true;
    }

    $scope.page_request = {
        'page_no': 1,
        'size': 25,
    }

    $scope.page_size_options = [25, 50, 100]

    $scope.paginationListener = function(newPageRequest, oldPageRequest){

        if(newPageRequest.page_no > 0 ){
            $scope.fetchData();
        }
    }

    $scope.toPreviousPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if(current_page_no > 1){
            $scope.page_request.page_no = $scope.page_request.page_no - 1;
        }
    }

    $scope.toNextPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if( current_page_no < $scope.paged_result.total_pages){
            $scope.page_request.page_no = $scope.page_request.page_no + 1;
        }
    }

    //setup the watch function for the pagination
    $scope.$watch('page_request', $scope.paginationListener, true)

 }])
 .controller('blocked_contactsController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
        $http.post('/blocked_contacts', $scope.page_request).success(function(data, status, headers, config){
            $scope.paged_result = data;
            $scope.records=$scope.paged_result.content;
        }).error(function(data, status, headers, config){
            alert('Unable to load records');
        });
    }

    $scope.add_new = function(){
        $scope.records.push({'contact': '', 'is_new': true});
    }

    $scope.save = function(record){
        $http.post('/blocked_contacts/save', record).success(function(data, status, headers, config){
            record.is_new = false;
            record.is_modify = false;
        }).error(function(data, status, headers, config){
            alert('Cannot save record');
        });
    }

    $scope.remove = function(index){
        var record = $scope.records[index];
        $http.post('/blocked_contacts/remove', record).success(function(data, status, headers, config){
            $scope.records.splice(index, 1);
        }).error(function(data, status, headers, config){
            alert('Cannot remove record');
        });
    }

    $scope.modify = function(index){
        var record = $scope.records[index];
        record.is_modify = true;
    }

    $scope.page_request = {
        'page_no': 1,
        'size': 25,
    }

    $scope.page_size_options = [25, 50, 100]

    $scope.paginationListener = function(newPageRequest, oldPageRequest){

        if(newPageRequest.page_no > 0 ){
            $scope.fetchData();
        }
    }

    $scope.toPreviousPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if(current_page_no > 1){
            $scope.page_request.page_no = $scope.page_request.page_no - 1;
        }
    }

    $scope.toNextPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if( current_page_no < $scope.paged_result.total_pages){
            $scope.page_request.page_no = $scope.page_request.page_no + 1;
        }
    }

    //setup the watch function for the pagination
    $scope.$watch('page_request', $scope.paginationListener, true)

 }])
 .controller('configsController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
        $http.get('/configs').success(function(data, status, headers, config){
            $scope.records=data;
        }).error(function(data, status, headers, config){
            alert('Unable to load records');
        });
    }

    $scope.fetchData();

 }])
 .controller('usersController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
        $http.post('/users', $scope.page_request).success(function(data, status, headers, config){
            $scope.paged_result = data;
            $scope.records=$scope.paged_result.content;
        }).error(function(data, status, headers, config){
            alert('Unable to load records');
        });
    }

     $scope.save = function(record){
        $http.post('/users/save', record).success(function(data, status, headers, config){
            record.is_modify = false;
        }).error(function(data, status, headers, config){
            alert('Cannot save record');
        });
    }

    $scope.remove = function(index){
        var record = $scope.records[index];
        $http.post('/users/remove', record).success(function(data, status, headers, config){
            $scope.records.splice(index, 1);
        }).error(function(data, status, headers, config){
            alert('Cannot remove record');
        });
    }

    $scope.modify = function(index){
        var record = $scope.records[index];
        record.is_modify = true;
    }

    $scope.page_request = {
        'page_no': 1,
        'size': 25,
    }

    $scope.page_size_options = [25, 50, 100]

    $scope.paginationListener = function(newPageRequest, oldPageRequest){

        if(newPageRequest.page_no > 0 ){
            $scope.fetchData();
        }
    }

    $scope.toPreviousPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if(current_page_no > 1){
            $scope.page_request.page_no = $scope.page_request.page_no - 1;
        }
    }

    $scope.toNextPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if( current_page_no < $scope.paged_result.total_pages){
            $scope.page_request.page_no = $scope.page_request.page_no + 1;
        }
    }

    //setup the watch function for the pagination
    $scope.$watch('page_request', $scope.paginationListener, true)


 }])
.controller('jobsController', ['$scope','$http', '$route', '$window', function($scope, $http, $route, $window) {
    $scope.fetchData = function(){
        $http.post('/jobs', $scope.page_request).success(function(data, status, headers, config){
            $scope.paged_result = data;
            $scope.jobs=data.content;
        }).error(function(data, status, headers, config){
            alert('Unable to load jobs');
        });
    }

    $scope.page_request = {
        'page_no': 1,
        'size': 25,
    }

    $scope.page_size_options = [25, 50, 100]

    $scope.paginationListener = function(newPageRequest, oldPageRequest){

        if(newPageRequest.page_no > 0 ){
            $scope.fetchData();
        }
    }

    $scope.toPreviousPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if(current_page_no > 1){
            $scope.page_request.page_no = $scope.page_request.page_no - 1;
        }
    }

    $scope.toNextPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if( current_page_no < $scope.paged_result.total_pages){
            $scope.page_request.page_no = $scope.page_request.page_no + 1;
        }
    }

    //setup the watch function for the pagination
    $scope.$watch('page_request', $scope.paginationListener, true)

    $scope.remove = function(job_item){
        $http.post('/jobs/remove', job_item).success(
            function(data, status, headers, config){
                //alert('Marked ' + contact.contact + ' as blocked contact');
                $window.location.reload();
            }
            ).error(function(data, status, headers, config){
                alert('Unable to remove ' + job_item.job_title);
            });
    }

    $scope.markAsBlockedContact = function(contact){
        $http.post('/blocked_contacts/save', contact).success(
            function(data, status, headers, config){
                //alert('Marked ' + contact.contact + ' as blocked contact');
                $window.location.reload();
            }
            ).error(function(data, status, headers, config){
                alert('Unable to mark ' + contact.contact + ' as blocked contact');
            });
    }

    $scope.loadBlockedContacts = function(){
        $http.get('/blocked_contacts').success(function(data, status, headers, config){
            $scope.agents = data;
        }).error(function(data, status, headers, config){
            alert('Unable to load agents list');
        });
    }

    $scope.isContactBlocked = function(contact){

        var isBlocked = false;
        angular.forEach($scope.agents, function(item, index){

            if( contact === item.contact ){
                isBlocked = true;
            }
        });

        return isBlocked;
    }

    $scope.loadBlockedContacts();
 }]);