<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up()
    {
        Schema::table('documents', function (Blueprint $table) {
            $table->string('file_id')->nullable()->after('status');
            $table->json('classifications')
                ->nullable()
                ->after('category')
                ->comment('Multi-level classification array from AI Service');
        });
    }

    public function down()
    {
        Schema::table('documents', function (Blueprint $table) {
            $table->dropColumn('classifications');
        });
    }
};