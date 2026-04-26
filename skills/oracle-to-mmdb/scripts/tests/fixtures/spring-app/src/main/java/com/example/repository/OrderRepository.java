package com.example.repository;

import com.example.entity.OrderEntity;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.Repository;

public interface OrderRepository extends Repository<OrderEntity, Long> {
    @Query(value = "SELECT * FROM ORDERS WHERE ROWNUM <= 10", nativeQuery = true)
    java.util.List<OrderEntity> findTopTen();
}
