/* eslint-env node */
module.exports = function ( grunt ) {
	grunt.loadNpmTasks( 'grunt-eslint' );
	grunt.loadNpmTasks( 'grunt-stylelint' );

	grunt.initConfig( {
		eslint: {
			options: {
				cache: true,
				fix: grunt.option( 'fix' )
			},
			all: '.'
		},
		stylelint: {
			options: {
				cache: true
			},
			all: [
				'static/css/*.{css,less}',
				'!static/css/thirdparty/**'
			]
		}
	} );

	grunt.registerTask( 'test', [ 'eslint', 'stylelint' ] );
	grunt.registerTask( 'default', 'test' );
};
