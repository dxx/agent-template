# 更新日志

## 2026-06-14

### 新增

- 新增 `FilesystemMiddleware`，提供本地文件系统相关工具。([8c40d98](https://github.com/dxx/agent-template/commit/8c40d9845aacba7499faef4a835561a9936847a3))
- 新增 `OPENAI_PROVIDER` 配置，用于按模型提供商生成差异化请求参数。([b42a882](https://github.com/dxx/agent-template/commit/b42a88234e51067a86b0ce8d786de8f4be4cf81e))

### 变更

- 完善 README 配置说明。([e6d5777](https://github.com/dxx/agent-template/commit/e6d57771f9e9ec4b683a665401e1358904fc283d), [e5ff2a8](https://github.com/dxx/agent-template/commit/e5ff2a8b8ae29a769d41fb82ed82fdd78a54d325))
- 根据模型提供商生成 `extra_body` 参数。([88fe581](https://github.com/dxx/agent-template/commit/88fe581ea1b1876cacc100ba9d83e29d6a6071d8))
- 为 `read_source_file` 增加路径校验，限制只能读取技能目录内文件。([ea52461](https://github.com/dxx/agent-template/commit/ea5246162e29beb91541f2f3210066a6227ec1fe))
- 统一调整 runtime 类型标注。([7198465](https://github.com/dxx/agent-template/commit/719846531c0e687364ca5b7111899fef3033b1ca))

## 2026-06-12

### 新增

- 新增 CORS 配置项。([d73fe2c](https://github.com/dxx/agent-template/commit/d73fe2c723479b36d4268779d6f7b1a3fcaa6f68))
- 接入 FastAPI `CORSMiddleware`。([14d123f](https://github.com/dxx/agent-template/commit/14d123f3948db29262bc19119794384aa7cecb2c))

### 变更

- 调整 `APP_ENV` 内部变量命名。([3b7a861](https://github.com/dxx/agent-template/commit/3b7a861e66c36ac606754457639aaee6eb4dce54))
- 调整 JSON 相关类型定义。([53cb240](https://github.com/dxx/agent-template/commit/53cb240f5b1da0fbf2896b30d224bfffae24aed1))

## 2026-06-09

### 变更

- 删除无用导入。([8615270](https://github.com/dxx/agent-template/commit/8615270d79af890f9776cbe3a950c4de01eb63a5))
- 调整 `JsonFormatter` 导入来源。([ddd320c](https://github.com/dxx/agent-template/commit/ddd320c00063decff265a4131932d67d39fb3e30))

## 2026-06-07

### 新增

- 新增多模态 API 测试示例。([de41692](https://github.com/dxx/agent-template/commit/de416923efabcf73a30f3e78faf82cf772865901))
- 新增多模态文档说明。([5d99564](https://github.com/dxx/agent-template/commit/5d9956490a311dedcc531730b8c5ee5de34afc52))
- 支持多模态消息内容处理。([bbb5d67](https://github.com/dxx/agent-template/commit/bbb5d67525b7db87139776a65b04c3a3de86f127), [a09ec34](https://github.com/dxx/agent-template/commit/a09ec34e24a208b9ff8447b572ba3087acd15b5f))

### 变更

- 调整 README 和相关文档。([f9f169d](https://github.com/dxx/agent-template/commit/f9f169d1e015ca0ee62bf89a9d60f5aded414e50), [eb1a64b](https://github.com/dxx/agent-template/commit/eb1a64bfad4f02a4ac6d7bac9cd60e35fd2ae776), [0d2142e](https://github.com/dxx/agent-template/commit/0d2142e507e1627bac702bc283a964e1e1ed39e1))
- 修改 `ChatResponse` 的内容类型。([f549b15](https://github.com/dxx/agent-template/commit/f549b1539d44cb4a1a1189c634e9be21a0b29616))
- 调整日志级别和日志内容。([0be6d1c](https://github.com/dxx/agent-template/commit/0be6d1c2ca3c26dbb578b8a8c2d9b55be469dd7c), [98f28e3](https://github.com/dxx/agent-template/commit/98f28e3353ce04d2d7dcd59d039291631785f934))
- 为 `ToolRuntime` 增加类型标注。([11825c1](https://github.com/dxx/agent-template/commit/11825c138b21d2bb7bcaf1c98d38df839b6fc762))
- 调整 MCP 示例。([0174fd7](https://github.com/dxx/agent-template/commit/0174fd7b750b691f8a93c74e1fa2a890b836b04e))
- 调整内容。([2e7315b](https://github.com/dxx/agent-template/commit/2e7315b04d425383383487ac27b0b2d9ce24e87f))

## 2026-06-06

### 新增

- 新增已注册 Agent 的日志信息。([8d18615](https://github.com/dxx/agent-template/commit/8d18615da503629dac087a05228628887172cb15))

### 变更

- 调整 Agent 实现。([cab0977](https://github.com/dxx/agent-template/commit/cab0977d76694c0b9de805eb3a8cbc9f585351b4))
- 更新文档。([70b5e18](https://github.com/dxx/agent-template/commit/70b5e181f91a8ed2dce10afa5509f3f946c637d5))

## 2026-06-05

### 变更

- 调整条件判断逻辑。([fb03be7](https://github.com/dxx/agent-template/commit/fb03be734ec3c317641c8f56aadb55fa33b1fcad))

## 2026-06-03

### 变更

- 调整配置。([7eda346](https://github.com/dxx/agent-template/commit/7eda346c4974ddd71a944fe94b5e9eb43024bf81))
- 更新 README。([afcc73b](https://github.com/dxx/agent-template/commit/afcc73b5cb8d75f44fe7536aaa629565c376a252))

## 2026-06-02

### 变更

- 修复逻辑判断问题。([0b0dd34](https://github.com/dxx/agent-template/commit/0b0dd345ed2a7e8bfba3a58113cdff33a7a8d813))

## 2026-06-01

### 新增

- 支持 `GraphInterrupt`。([e7bf91e](https://github.com/dxx/agent-template/commit/e7bf91ed3986bdb1701b4e10d254869084fe1e7d))

### 变更

- 重构子代理实现。([2081451](https://github.com/dxx/agent-template/commit/20814519bd9eec6a2275973c3b3779ddb230f71b))
- 调整路由方法名称和方法签名。([372ea26](https://github.com/dxx/agent-template/commit/372ea269666c61fa286963de74a93a63bc8d259f), [5e1ddbe](https://github.com/dxx/agent-template/commit/5e1ddbe320f5a778446c34851fd517070e52d732))
- 更新 README 和相关文档。([5500887](https://github.com/dxx/agent-template/commit/550088750b44316552470784d408fef9a0c5e22f), [c13cf75](https://github.com/dxx/agent-template/commit/c13cf75308fdb84eed19c02eeacfc9507521e67d), [d6c80cf](https://github.com/dxx/agent-template/commit/d6c80cffc370e398f653e8ddb12759bf9571e03d), [f07ec9e](https://github.com/dxx/agent-template/commit/f07ec9e648a99818b2e28be988d28ad6ea542df1), [2b3ba0b](https://github.com/dxx/agent-template/commit/2b3ba0b9b99536bcdff5a389d233e883177eff11), [2d4bd37](https://github.com/dxx/agent-template/commit/2d4bd37be3b64a161673bb6201f935c6c4f6f592))

## 2026-05-31

### 新增

- 新增 HTTP 请求测试 API。([cafde0d](https://github.com/dxx/agent-template/commit/cafde0dda5e609450dc665ec4d7a736c84e14f5c))
- 新增路由模式。([4ff101c](https://github.com/dxx/agent-template/commit/4ff101cdfdb1778b66b6531c9cf0d7ce6ffe3a23))
- 新增 `nostream` 标签。([9f37486](https://github.com/dxx/agent-template/commit/9f374861c50da982bf50a8f3b294787675a8dfd8))

## 2026-05-30

### 新增

- 新增工具调用错误处理。([3936994](https://github.com/dxx/agent-template/commit/39369944717c95892d58ed7683a56f640bd6be6b))

### 变更

- 更新 README 和相关文档。([06378aa](https://github.com/dxx/agent-template/commit/06378aae883ae1a173377284f665a706e75894b2), [d58db7f](https://github.com/dxx/agent-template/commit/d58db7f6bfbd8b26d6d9cff778a453a4b14d839b))

## 2026-05-27

### 变更

- 使用 `BaseModel` 的 JSON 序列化方法。([1ee3c22](https://github.com/dxx/agent-template/commit/1ee3c22ecfb88503cb73b5ee4be00a8f43e329d3))

## 2026-05-26

### 变更

- 调整 `created` 字段。([6c12acc](https://github.com/dxx/agent-template/commit/6c12accf1e6b718d01b733924983f08eab470ca0))
- 删除无用导入。([1dbb1b6](https://github.com/dxx/agent-template/commit/1dbb1b654c5efd30e53da3c93e974bd5848f5b4e))

## 2026-05-25

### 变更

- 调整 checkpoint 和 store 逻辑。([e5e15f5](https://github.com/dxx/agent-template/commit/e5e15f50093fc98593ce6ff0705d64304eb88413))
- 更新 README。([0e1b9c8](https://github.com/dxx/agent-template/commit/0e1b9c80595f29fc4a4af63e94f7d161213c52ed))

## 2026-05-23

### 新增

- 使用 store 存储消息记录。([c4e18ac](https://github.com/dxx/agent-template/commit/c4e18ac18c13beca5cc117f1a77cc7d58467b28f))

### 变更

- 删除无用导入和文档注释。([87e438a](https://github.com/dxx/agent-template/commit/87e438a69127213d406f33e2f1ce896e57755b20))
- 更新文档。([2e45eab](https://github.com/dxx/agent-template/commit/2e45eabb89a989677d25fb83232bcf3ac4fbe7be))

## 2026-05-10

### 新增

- 新增 build-system 配置。([88aa292](https://github.com/dxx/agent-template/commit/88aa292d4e80324a3e0dd4b1e6091f83facc4a62))

### 变更

- 重构环境变量配置逻辑。([79568ab](https://github.com/dxx/agent-template/commit/79568abe497fb8728ca57ef65825be60e3d0ae16))
- 移除 `AppEnv.DEFAULT` 判断。([fd40256](https://github.com/dxx/agent-template/commit/fd4025661a46c92f377c6998b63a4f107f2a4497))
- 调整 API code。([49e4bc1](https://github.com/dxx/agent-template/commit/49e4bc122dfb0662d91e0b1ed75af900f33b1da1))
- 调整 process 消息内容。([4e01c7c](https://github.com/dxx/agent-template/commit/4e01c7cb9464f2df5a121aeea135db6908a60b03))
- 更新 README 和相关文档。([f413c3e](https://github.com/dxx/agent-template/commit/f413c3ec7695040d8ef01956d5d88fd34abc9a8c), [3a32bbe](https://github.com/dxx/agent-template/commit/3a32bbe56b4c4072806485c7bd6ccadaabd05fcf))

### 依赖

- 更新 `uv.lock`。([9864fad](https://github.com/dxx/agent-template/commit/9864fad98ff8fbf03accaeee6c84d7d0b24ac708))

## 2026-05-08

### 变更

- 处理 `APP_INV` 相关逻辑。([86ca449](https://github.com/dxx/agent-template/commit/86ca449b6ea206071dd366cd41eb4dcd1f24c4ec))

## 2026-05-05

### 变更

- 更新项目描述。([e316932](https://github.com/dxx/agent-template/commit/e3169325c2fdb7eaa3a1b4fb3b8d83bfd3eab5a7))

## 2026-04-29

### 变更

- 将双引号调整为单引号。([d352c4f](https://github.com/dxx/agent-template/commit/d352c4f5185fe974da65533a24ff0c7f8db68999))

## 2026-04-25

### 依赖

- 新增 `uv.lock`。([84f7b69](https://github.com/dxx/agent-template/commit/84f7b69b37d1709a4e89685f16297fd4530ba690))

## 2026-04-20

### 变更

- 将项目命名从 ai 调整为 agent。([b0f9d2d](https://github.com/dxx/agent-template/commit/b0f9d2d53692dd2c908de9bf8838f1b3c855fc86))

## 2026-04-19

### 变更

- 抽取 `run` 函数。([1eab5a9](https://github.com/dxx/agent-template/commit/1eab5a9833fd4b54b9566e2f0046817591f00bbd))

## 2026-04-18

### 新增

- 新增文档和测试示例。([de870d0](https://github.com/dxx/agent-template/commit/de870d0c44ba8fb9d51abb6082d7db88f8fa72aa), [fbc9ba2](https://github.com/dxx/agent-template/commit/fbc9ba28aac6833d286707cbab5d9663d31df12c))
- 新增对话 `chat_id` 校验。([f5a4ecc](https://github.com/dxx/agent-template/commit/f5a4ecc2545c5f027822870c8a1223f948dcf5a5))

### 变更

- 重新实现工具调用补丁逻辑。([cc49976](https://github.com/dxx/agent-template/commit/cc49976f73887f01fed47ff713ff3a27d7e06561))
- 调整枚举值。([a6830d0](https://github.com/dxx/agent-template/commit/a6830d00eba8c5af896c4f366a50a672b5cea6f2))
- 格式化代码。([40f43d6](https://github.com/dxx/agent-template/commit/40f43d64d1bcfee22ae89c47549eb7b70e042ea9))
- 更新 README 和相关文档。([7f4df1f](https://github.com/dxx/agent-template/commit/7f4df1f504d9bde6875a236146e24e3a6567a935), [6c859b2](https://github.com/dxx/agent-template/commit/6c859b228253ef407b7c038afcd1e3fad515c0dd), [36b652a](https://github.com/dxx/agent-template/commit/36b652afbcba86d4d0a43283840f389995ba0ab8), [d0ec86c](https://github.com/dxx/agent-template/commit/d0ec86c478cc7ba4a2fe127133d5618ab61c5f55), [0d6bd7f](https://github.com/dxx/agent-template/commit/0d6bd7f8a8cb3516fbd573d214e41d559785421e), [4af49ca](https://github.com/dxx/agent-template/commit/4af49cae05b79bb5d26e06e62217a8f73a93080c))

## 2026-04-17

### 新增

- 新增 MCP 中间件。([9d63967](https://github.com/dxx/agent-template/commit/9d63967ec6d8e332d3cf1ad82f0a320eced9913e))
- 接入 `MCPClientMiddleware`。([21c846d](https://github.com/dxx/agent-template/commit/21c846d96a87d54788a367ccdfa1cfa0991107ab))

### 变更

- 删除重复导入。([6f1eeda](https://github.com/dxx/agent-template/commit/6f1eeda26de3620e11fde0f8274052678a87e70c), [d3ba490](https://github.com/dxx/agent-template/commit/d3ba490787d8426719ac8c4f521533e332c1dd73))
- 更新 README。([0d94b5e](https://github.com/dxx/agent-template/commit/0d94b5ea150c43f2485d52cbf42d77a27d9d8414))

## 2026-04-16

### 新增

- 新增 `prebuild` 模块。([7341132](https://github.com/dxx/agent-template/commit/7341132eecba86e6339b6b4cf73cc6bdfb601295))
- Skills 内置 `read_source_file` 工具。([83ea4f0](https://github.com/dxx/agent-template/commit/83ea4f0ed4d9eb58300d28c5900959d4d0496d94))
- 新增消息相关接口。([0b80ba7](https://github.com/dxx/agent-template/commit/0b80ba7b3ae50a07fec4f61da1049abd9a910e94))
- 支持通过 HTTP Header 传递用户 token。([340b777](https://github.com/dxx/agent-template/commit/340b777569c141f6f574821f53e6809a7970f0f6))

### 变更

- 使用全局 memory。([cd117ea](https://github.com/dxx/agent-template/commit/cd117ea31ce1f3cec08b2c62f5c3e693cfe86adb))
- 使用 `prebuild` 模块。([2cc188c](https://github.com/dxx/agent-template/commit/2cc188c365eba5edb5564229e01e53fa74635c8d))
- 修复类型检查错误。([5549bbd](https://github.com/dxx/agent-template/commit/5549bbd543fb7f6d603928b35cb089de7e6305a4))
- 调整 `type ignore`。([c2beb22](https://github.com/dxx/agent-template/commit/c2beb22ee5f64686027b27750ed36cbd7f1953f5))
- 调整注释。([7ed2511](https://github.com/dxx/agent-template/commit/7ed25116453b33f00228b16d5467d1575fc444e2))
- 更新 README 和相关文档。([90b3434](https://github.com/dxx/agent-template/commit/90b34343d226969c6aeab5ae360fd2afebb792eb), [0dc0659](https://github.com/dxx/agent-template/commit/0dc06599117663ef26b796e84649cbd4211a77f2), [3fa6f14](https://github.com/dxx/agent-template/commit/3fa6f1403ab7f0e9717d29a609b0e08fafb9c389))

## 2026-04-15

### 新增

- 新增 `chat_id`。([129a762](https://github.com/dxx/agent-template/commit/129a762eff7e9519e03f531399bbcc7e4f61b028))
- 新增长期记忆能力。([8c399ab](https://github.com/dxx/agent-template/commit/8c399abdc6b65bd37e910a4a27f449ac0b5621a1))
- 使用异步工具。([9e3b142](https://github.com/dxx/agent-template/commit/9e3b1429b5338f9ddbb01804ffee3d2b6a5c2387))

### 变更

- 使用函数创建 memory。([9d83149](https://github.com/dxx/agent-template/commit/9d83149077e102b3ee921c02ec5e8144a0d0b20f))
- 移除 `print` 调用。([3f76a69](https://github.com/dxx/agent-template/commit/3f76a69f01a0cb7b9a82dbcadf890d5ae2c8c78b))
- 更新 README。([ae18744](https://github.com/dxx/agent-template/commit/ae1874452512f1f0ff3813f89b331ca39eb792e3))

## 2026-04-14

### 新增

- 为连接池增加参数。([e61f26f](https://github.com/dxx/agent-template/commit/e61f26f7380e6575910e6e99eb17366ae72ae94a))

### 变更

- 调整注释。([3eaf43d](https://github.com/dxx/agent-template/commit/3eaf43d880999e58f9399e99baf9b6bbe5670ec6))
- 移除不必要的 `parse_docstring` 参数。([d2a8994](https://github.com/dxx/agent-template/commit/d2a8994d98a90af796ad7a07966c31a9e8ca4d60))
- 更新日志级别说明。([273faf1](https://github.com/dxx/agent-template/commit/273faf15a04234ac38bbd134dc8eeb993fc86192))

## 2026-04-12

### 新增

- 初始化项目。([65331c6](https://github.com/dxx/agent-template/commit/65331c658093227dff873c0c17e33b64dcf256bd), [ad7fb09](https://github.com/dxx/agent-template/commit/ad7fb09ea96c45ec11d2947b1250b8a5cdd9f192))
- 新增 `.gitignore`。([bff831c](https://github.com/dxx/agent-template/commit/bff831c9b63c71a60fe3a0dcd6045dd56b9f5fbd))
- 新增 README。([351af86](https://github.com/dxx/agent-template/commit/351af86d7f2a5ec5b116f977a7dab0edaf6dd327))
- 支持 task 工具并行调用。([23c6192](https://github.com/dxx/agent-template/commit/23c6192f0451b6f7ad726b7ebd7f222f4366b6d6))

### 变更

- 补充错误堆栈信息。([78e54ce](https://github.com/dxx/agent-template/commit/78e54ce09f8b4895a9d4b55a21e5fea8b5c95be8))
- 调整相对路径使用的工作目录。([43803bf](https://github.com/dxx/agent-template/commit/43803bf4e9b6886423e3ef0c59795628ba2722c5))
- 更新 README。([558d2c5](https://github.com/dxx/agent-template/commit/558d2c5c8fb4f57c10bc117bc0f99d2ab78e48cf), [766e904](https://github.com/dxx/agent-template/commit/766e90479663d7b94e3ba697d920b690dd29b753))
