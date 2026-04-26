# Configuration Changes: Oracle -> MariaDB

## pom.xml

Full migration: remove ojdbc, add mariadb-java-client. Partial migration: keep both.

```xml
<!-- REMOVE for full migration / KEEP for partial migration -->
<dependency>
    <groupId>com.oracle.database.jdbc</groupId>
    <artifactId>ojdbc8</artifactId>
</dependency>

<!-- ADD in all cases -->
<dependency>
    <groupId>org.mariadb.jdbc</groupId>
    <artifactId>mariadb-java-client</artifactId>
    <version>3.3.3</version>
</dependency>
```

---

## application.yml -- Full Migration

```yaml
spring:
  datasource:
    url: jdbc:mariadb://hostname:3306/mydb?useUnicode=true&characterEncoding=utf8mb4&useSSL=false&serverTimezone=Asia/Taipei
    username: myuser
    password: mypassword
    driver-class-name: org.mariadb.jdbc.Driver
  jpa:
    hibernate:
      ddl-auto: none
    # Remove any Oracle dialect and let Spring Boot auto-detect, or set explicitly:
    database-platform: org.hibernate.dialect.MariaDBDialect
    # Remove these Oracle-specific Hibernate properties if present:
    # hibernate.temp.use_jdbc_metadata_defaults: false
    # hibernate.dialect: org.hibernate.dialect.Oracle12cDialect
mybatis:
  mapper-locations: classpath:mapper/**/*.xml
  type-aliases-package: com.example.domain
  configuration:
    map-underscore-to-camel-case: true
    default-fetch-size: 100
    default-statement-timeout: 30
    jdbc-type-for-null: OTHER
```

---

## Dual Datasource Setup (Partial Migration)

### application.yml

```yaml
spring:
  datasource:
    mariadb:
      url: jdbc:mariadb://hostname:3306/mydb?useUnicode=true&characterEncoding=utf8mb4&useSSL=false&serverTimezone=Asia/Taipei
      username: mariadb_user
      password: mariadb_pass
      driver-class-name: org.mariadb.jdbc.Driver
      hikari:
        pool-name: MariaDBPool
        maximum-pool-size: 20
        minimum-idle: 5
        connection-timeout: 30000
        idle-timeout: 600000
        max-lifetime: 1800000
        connection-test-query: SELECT 1
    oracle:
      url: jdbc:oracle:thin:@//hostname:1521/servicename
      username: oracle_user
      password: oracle_pass
      driver-class-name: oracle.jdbc.OracleDriver
      hikari:
        pool-name: OraclePool
        maximum-pool-size: 10
        minimum-idle: 2
```

### MariaDB DataSource Config Bean

```java
@Configuration
@MapperScan(basePackages = "com.example.mapper.mariadb",
            sqlSessionFactoryRef = "mariadbSqlSessionFactory")
@EnableJpaRepositories(
        basePackages = "com.example.repository.mariadb",
        entityManagerFactoryRef = "mariadbEntityManagerFactory",
        transactionManagerRef = "mariadbTransactionManager"
)
public class MariaDBDataSourceConfig {

    @Primary
    @Bean(name = "mariadbDataSource")
    @ConfigurationProperties("spring.datasource.mariadb")
    public DataSource mariadbDataSource() {
        return DataSourceBuilder.create().build();
    }

    // --- MyBatis ---
    @Primary
    @Bean(name = "mariadbSqlSessionFactory")
    public SqlSessionFactory mariadbSqlSessionFactory(
            @Qualifier("mariadbDataSource") DataSource ds) throws Exception {
        SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
        factory.setDataSource(ds);
        factory.setMapperLocations(new PathMatchingResourcePatternResolver()
                .getResources("classpath:mapper/mariadb/**/*.xml"));
        org.apache.ibatis.session.Configuration cfg =
                new org.apache.ibatis.session.Configuration();
        cfg.setMapUnderscoreToCamelCase(true);
        cfg.setDefaultFetchSize(100);
        cfg.setDefaultStatementTimeout(30);
        factory.setConfiguration(cfg);
        return factory.getObject();
    }

    // --- Spring Data JPA ---
    @Primary
    @Bean(name = "mariadbEntityManagerFactory")
    public LocalContainerEntityManagerFactoryBean mariadbEntityManagerFactory(
            EntityManagerFactoryBuilder builder,
            @Qualifier("mariadbDataSource") DataSource ds) {
        Map<String, Object> props = new HashMap<>();
        props.put("hibernate.dialect", "org.hibernate.dialect.MariaDBDialect");
        props.put("hibernate.hbm2ddl.auto", "none");
        return builder
                .dataSource(ds)
                .packages("com.example.entity.mariadb")
                .persistenceUnit("mariadb")
                .properties(props)
                .build();
    }

    // --- Transaction Manager ---
    // Note: JpaTransactionManager supports both JPA and MyBatis on the same DataSource natively
    @Primary
    @Bean(name = "mariadbTransactionManager")
    public PlatformTransactionManager mariadbTransactionManager(
            @Qualifier("mariadbEntityManagerFactory") EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }
}
```

### Oracle DataSource Config Bean

```java
@Configuration
@MapperScan(basePackages = "com.example.mapper.oracle",
            sqlSessionFactoryRef = "oracleSqlSessionFactory")
@EnableJpaRepositories(
        basePackages = "com.example.repository.oracle",
        entityManagerFactoryRef = "oracleEntityManagerFactory",
        transactionManagerRef = "oracleTransactionManager"
)
public class OracleDataSourceConfig {

    @Bean(name = "oracleDataSource")
    @ConfigurationProperties("spring.datasource.oracle")
    public DataSource oracleDataSource() {
        return DataSourceBuilder.create().build();
    }

    // --- MyBatis ---
    @Bean(name = "oracleSqlSessionFactory")
    public SqlSessionFactory oracleSqlSessionFactory(
            @Qualifier("oracleDataSource") DataSource ds) throws Exception {
        SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
        factory.setDataSource(ds);
        factory.setMapperLocations(new PathMatchingResourcePatternResolver()
                .getResources("classpath:mapper/oracle/**/*.xml"));
        org.apache.ibatis.session.Configuration cfg =
                new org.apache.ibatis.session.Configuration();
        cfg.setMapUnderscoreToCamelCase(true);
        factory.setConfiguration(cfg);
        return factory.getObject();
    }

    // --- Spring Data JPA ---
    @Bean(name = "oracleEntityManagerFactory")
    public LocalContainerEntityManagerFactoryBean oracleEntityManagerFactory(
            EntityManagerFactoryBuilder builder,
            @Qualifier("oracleDataSource") DataSource ds) {
        Map<String, Object> props = new HashMap<>();
        props.put("hibernate.dialect", "org.hibernate.dialect.Oracle12cDialect");
        props.put("hibernate.hbm2ddl.auto", "none");
        return builder
                .dataSource(ds)
                .packages("com.example.entity.oracle")
                .persistenceUnit("oracle")
                .properties(props)
                .build();
    }

    // --- Transaction Manager ---
    @Bean(name = "oracleTransactionManager")
    public PlatformTransactionManager oracleTransactionManager(
            @Qualifier("oracleEntityManagerFactory") EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }
}
```

### Directory Layout

```
src/main/
  java/com/example/
    entity/
      mariadb/
      oracle/
    repository/
      mariadb/            <- scanned by mariadbEntityManagerFactory
      oracle/             <- scanned by oracleEntityManagerFactory
    mapper/
      mariadb/            <- scanned by mariadbSqlSessionFactory
      oracle/             <- scanned by oracleSqlSessionFactory
  resources/mapper/
    mariadb/
    oracle/
```

### Transaction Routing

```java
@Transactional                                // MariaDB (Primary)
@Transactional("oracleTransactionManager")    // Oracle (explicit)

// TODO: CROSS-DB TRANSACTION RISK
// Writes to both -- NOT atomic. Options: JTA, compensating logic, restructure.
@Transactional
public void process(Long id) {
    orderMapper.update(id);   // MariaDB - covered
    invoiceMapper.mark(id);   // Oracle  - NOT covered
}
```

---

## JPA Namespace: javax vs jakarta

Spring Boot 2.x uses `javax.persistence.*`. Spring Boot 3.x migrated to `jakarta.persistence.*`.

```java
// Spring Boot 2.x
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;

// Spring Boot 3.x
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
```

**Rules:**
- Do NOT mix javax and jakarta imports in the same compiled module — it will fail at startup
- If migrating Oracle → MariaDB AND upgrading Spring Boot 2 → 3 simultaneously, do the namespace
  rename in the same commit as the datasource change to avoid a broken intermediate state

---

## URL Parameters Reference

| Parameter | Value | Notes |
|-----------|-------|-------|
| useUnicode | true | Enable Unicode |
| characterEncoding | utf8mb4 | Full Unicode including emoji |
| useSSL | false/true | false=dev, true=prod |
| serverTimezone | Asia/Taipei or UTC | Match server TZ |
| allowMultiQueries | false | Security |
| connectTimeout | 10000 | ms |
| socketTimeout | 30000 | ms |
