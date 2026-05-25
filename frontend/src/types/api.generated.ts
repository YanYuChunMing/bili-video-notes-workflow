export interface paths {
    "/api/tasks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tasks */
        get: operations["list_tasks_api_tasks_get"];
        put?: never;
        /** Create Task */
        post: operations["create_task_api_tasks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/tasks/{task_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Task */
        get: operations["get_task_api_tasks__task_id__get"];
        put?: never;
        post?: never;
        /** Delete Task */
        delete: operations["delete_task_api_tasks__task_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/outputs/{task_id}/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Summary */
        get: operations["get_summary_api_outputs__task_id__summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/outputs/{task_id}/mindmap": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Mindmap */
        get: operations["get_mindmap_api_outputs__task_id__mindmap_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/outputs/{task_id}/mindmap.html": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Mindmap Html */
        get: operations["get_mindmap_html_api_outputs__task_id__mindmap_html_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/outputs/{task_id}/transcript": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Transcript */
        get: operations["get_transcript_api_outputs__task_id__transcript_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/outputs/{task_id}/transcript-punct": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Transcript Punct */
        get: operations["get_transcript_punct_api_outputs__task_id__transcript_punct_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/outputs/{task_id}/transcript-images": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Transcript Images */
        get: operations["get_transcript_images_api_outputs__task_id__transcript_images_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/outputs/{task_id}/metadata": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Metadata */
        get: operations["get_metadata_api_outputs__task_id__metadata_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/config": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Config */
        get: operations["get_config_api_config_get"];
        /** Update Config */
        put: operations["update_config_api_config_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/config/check": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Check Api Key */
        get: operations["check_api_key_api_config_check_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/media/{task_id}/{filepath}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Serve Media */
        get: operations["serve_media_media__task_id___filepath__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health Check */
        get: operations["health_check_api_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}


export type webhooks = Record<string, never>;


export interface components {
    schemas: {
        /** ApiResponse */
        ApiResponse: {
            /**
             * Code
             * @default 0
             */
            code: number;
            /**
             * Message
             * @default success
             */
            message: string;
            /** Data */
            data?: unknown | null;
        };
        /** ConfigUpdateRequest */
        ConfigUpdateRequest: {
            /** Whisper Model */
            whisper_model?: string | null;
            /** Whisper Language */
            whisper_language?: string | null;
            /** Whisper Device */
            whisper_device?: string | null;
            /** Whisper Compute Type */
            whisper_compute_type?: string | null;
            /** Deepseek Model */
            deepseek_model?: string | null;
            /** Deepseek Base Url */
            deepseek_base_url?: string | null;
            /** Deepseek Api Key */
            deepseek_api_key?: string | null;
            /** Screenshot Enabled */
            screenshot_enabled?: boolean | null;
            /** Screenshot Strategy */
            screenshot_strategy?: string | null;
            /** Screenshot Min Interval Seconds */
            screenshot_min_interval_seconds?: number | null;
            /** Screenshot Max Avg Per Minute */
            screenshot_max_avg_per_minute?: number | null;
            /** Screenshot Difference Threshold */
            screenshot_difference_threshold?: number | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** TaskCreateRequest */
        TaskCreateRequest: {
            /** Urls */
            urls: string[];
            /** @default basic */
            mode: components["schemas"]["TaskMode"];
        };
        /**
         * TaskMode
         * @enum {string}
         */
        TaskMode: "basic" | "with_images";
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** TaskInfo */
        TaskInfo: {
            /** Task Id */
            task_id: string;
            /** Url */
            url: string;
            /**
             * Title
             * @default
             */
            title: string;
            mode: components["schemas"]["TaskMode"];
            /** @default pending */
            status: components["schemas"]["TaskStatus"];
            /**
             * Progress
             * @default 0
             */
            progress: number;
            /**
             * Stage Message
             * @default
             */
            stage_message: string;
            /**
             * Output Dir
             * @default
             */
            output_dir: string;
            /**
             * Error Message
             * @default
             */
            error_message: string;
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Completed At
             * @default
             */
            completed_at: string;
            $defs: {
                /**
                 * TaskMode
                 * @enum {string}
                 */
                TaskMode: "basic" | "with_images";
                /**
                 * TaskStatus
                 * @enum {string}
                 */
                TaskStatus: "pending" | "downloading" | "transcribing" | "cleaning" | "summarizing" | "mindmap" | "screenshot" | "completed" | "failed";
            };
        };
        /** ConfigDisplay */
        ConfigDisplay: {
            project: components["schemas"]["ProjectConfig"];
            whisper: components["schemas"]["WhisperConfig"];
            deepseek: components["schemas"]["DeepseekConfig"];
            screenshot: components["schemas"]["ScreenshotConfig"];
            $defs: {
                /** DeepseekConfig */
                DeepseekConfig: {
                    /** Model */
                    model: string;
                    /** Base Url */
                    base_url: string;
                    /**
                     * Has Api Key
                     * @default false
                     */
                    has_api_key: boolean;
                    /**
                     * Max Chunk Minutes
                     * @default 12
                     */
                    max_chunk_minutes: number;
                };
                /** ProjectConfig */
                ProjectConfig: {
                    /** Name */
                    name: string;
                    /** Output Dir */
                    output_dir: string;
                    /** Log Dir */
                    log_dir: string;
                    /** Temp Dir */
                    temp_dir: string;
                    /** Download Dir */
                    download_dir: string;
                };
                /** ScreenshotConfig */
                ScreenshotConfig: {
                    /**
                     * Enabled
                     * @default false
                     */
                    enabled: boolean;
                    /**
                     * Strategy
                     * @default learning
                     */
                    strategy: string;
                    /**
                     * Min Interval Seconds
                     * @default 3
                     */
                    min_interval_seconds: number;
                    /**
                     * Max Avg Per Minute
                     * @default 6
                     */
                    max_avg_per_minute: number;
                    /**
                     * Max Images Per Unit
                     * @default 2
                     */
                    max_images_per_unit: number;
                    /**
                     * Difference Threshold
                     * @default 0.85
                     */
                    difference_threshold: number;
                };
                /** WhisperConfig */
                WhisperConfig: {
                    /** Model */
                    model: string;
                    /** Language */
                    language: string;
                    /** Device */
                    device: string;
                    /**
                     * Compute Type
                     * @default auto
                     */
                    compute_type: string;
                };
            };
        };
        /** WhisperConfig */
        WhisperConfig: {
            /** Model */
            model: string;
            /** Language */
            language: string;
            /** Device */
            device: string;
            /**
             * Compute Type
             * @default auto
             */
            compute_type: string;
        };
        /** DeepseekConfig */
        DeepseekConfig: {
            /** Model */
            model: string;
            /** Base Url */
            base_url: string;
            /**
             * Has Api Key
             * @default false
             */
            has_api_key: boolean;
            /**
             * Max Chunk Minutes
             * @default 12
             */
            max_chunk_minutes: number;
        };
        /** ScreenshotConfig */
        ScreenshotConfig: {
            /**
             * Enabled
             * @default false
             */
            enabled: boolean;
            /**
             * Strategy
             * @default learning
             */
            strategy: string;
            /**
             * Min Interval Seconds
             * @default 3
             */
            min_interval_seconds: number;
            /**
             * Max Avg Per Minute
             * @default 6
             */
            max_avg_per_minute: number;
            /**
             * Max Images Per Unit
             * @default 2
             */
            max_images_per_unit: number;
            /**
             * Difference Threshold
             * @default 0.85
             */
            difference_threshold: number;
        };
        /** ProjectConfig */
        ProjectConfig: {
            /** Name */
            name: string;
            /** Output Dir */
            output_dir: string;
            /** Log Dir */
            log_dir: string;
            /** Temp Dir */
            temp_dir: string;
            /** Download Dir */
            download_dir: string;
        };
        /** ApiKeyStatus */
        ApiKeyStatus: {
            /** Valid */
            valid: boolean;
            /**
             * Message
             * @default
             */
            message: string;
        };
        /** VideoMetadata */
        VideoMetadata: {
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Duration
             * @default 0
             */
            duration: number;
            /**
             * Uploader
             * @default
             */
            uploader: string;
            /**
             * Upload Date
             * @default
             */
            upload_date: string;
            /**
             * Description
             * @default
             */
            description: string;
            /**
             * Webpage Url
             * @default
             */
            webpage_url: string;
        };
        /**
         * TaskStatus
         * @enum {string}
         */
        TaskStatus: "pending" | "downloading" | "transcribing" | "cleaning" | "summarizing" | "mindmap" | "screenshot" | "completed" | "failed";
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}


export type $defs = Record<string, never>;


export interface operations {
    list_tasks_api_tasks_get: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_task_api_tasks_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TaskCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_task_api_tasks__task_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_task_api_tasks__task_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_summary_api_outputs__task_id__summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_mindmap_api_outputs__task_id__mindmap_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_mindmap_html_api_outputs__task_id__mindmap_html_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_transcript_api_outputs__task_id__transcript_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_transcript_punct_api_outputs__task_id__transcript_punct_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_transcript_images_api_outputs__task_id__transcript_images_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_metadata_api_outputs__task_id__metadata_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_config_api_config_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    update_config_api_config_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConfigUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    check_api_key_api_config_check_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse"];
                };
            };
        };
    };
    serve_media_media__task_id___filepath__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: string;
                filepath: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_check_api_status_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse"];
                };
            };
        };
    };
}
